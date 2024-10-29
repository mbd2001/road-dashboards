from functools import reduce
from operator import mul

from pypika import Criterion, EmptyCriterion, Query, Tuple, functions
from pypika.queries import QueryBuilder
from pypika.terms import Term
from road_dump_dashboard.table_schemes.base import Base, Column
from road_dump_dashboard.table_schemes.meta_data import MetaData


def base_data_subquery(
    main_tables: list[Base],
    terms: list[Term],
    meta_data_tables: list[Base] = None,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
    intersection_on: bool = False,
) -> QueryBuilder:
    intersection_filter = get_intersection_filter(meta_data_tables, intersection_on)
    filters = Criterion.all([data_filter, page_filters, intersection_filter])
    joint_tables = [
        join_main_and_md(main_table, md_table)
        .select(*resolve_unambiguous(md_table, terms))
        .where(*resolve_unambiguous(md_table, [filters]))
        # .where(*resolve_unambiguous(md_table, [EmptyCriterion()]))
        for main_table, md_table in zip(main_tables, meta_data_tables)
    ]
    union_table = union_all_query_list(joint_tables)
    return union_table


def resolve_unambiguous(md_table: Base, terms: list[Term]) -> list[Term]:
    return [term.replace_table(current_table=None, new_table=md_table) for term in terms]


def get_intersection_filter(meta_data_tables: list[Base], intersection_on: bool):
    if not intersection_on:
        return EmptyCriterion()

    return Tuple(MetaData.clip_name, MetaData.grabindex).isin(
        intersect_query_list(
            [Query.from_(md_table).select(md_table.clip_name, md_table.grabindex) for md_table in meta_data_tables]
        )
    )


def join_main_and_md(main_table: Base, md_table: Base):
    if not md_table or (md_table == main_table):
        return Query.from_(main_table)

    return (
        Query.from_(main_table)
        .inner_join(md_table)
        .on((main_table.clip_name == md_table.clip_name) & (main_table.grabindex == md_table.grabindex))
    )


def union_all_query_list(query_list: list[QueryBuilder]) -> QueryBuilder:
    ret = reduce(mul, query_list)
    return ret


def intersect_query_list(query_list: list[QueryBuilder]) -> QueryBuilder:
    queries_iter = iter(query_list)
    final_query = next(queries_iter)
    while curr_query := next(queries_iter, None):
        final_query = curr_query.intersect(curr_query)

    return final_query


def conf_mat_subquery(
    diff_column: Column,
    main_labels: list[Base],
    secondary_labels: list[Base],
    main_md: list[Base] = None,
    secondary_md: list[Base] = None,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
):
    terms = [diff_column, MetaData.clip_name, MetaData.grabindex, MetaData.obj_id]
    main_subquery = base_data_subquery(
        main_tables=main_labels,
        terms=terms,
        meta_data_tables=main_md,
        data_filter=data_filter,
        page_filters=page_filters,
    )
    secondary_subquery = base_data_subquery(
        main_tables=secondary_labels,
        terms=terms,
        meta_data_tables=secondary_md,
        data_filter=data_filter,
        page_filters=page_filters,
    )
    first_diff_col = diff_column.replace_table(None, main_subquery)
    second_diff_col = diff_column.replace_table(None, secondary_subquery)
    joined_query = (
        Query.from_(main_subquery)
        .inner_join(secondary_subquery)
        .on(
            (main_subquery.clip_name == secondary_subquery.clip_name)
            & (main_subquery.grabindex == secondary_subquery.grabindex)
            & (main_subquery.obj_id == secondary_subquery.obj_id)
        )
        .groupby(first_diff_col, second_diff_col)
        .select(first_diff_col.as_("main_val"), second_diff_col.as_("secondary_val"), functions.Count("*", "overall"))
    )
    return joined_query


DIFF_IDS_QUERY = """
    SELECT A.clip_name, A.grabindex
    FROM ({main_data}) A INNER JOIN ({secondary_data}) B
    ON ((A.clip_name = B.clip_name) AND (A.grabindex = B.grabindex) AND (A.obj_id = B.obj_id))
    WHERE A.{column_to_compare} != B.{column_to_compare}
    GROUP BY A.clip_name, A.grabindex   
    LIMIT {limit}
"""

DIFF_LABELS_QUERY = """
    WITH t1 AS (
        {diff_ids_query}
    )
    SELECT t2.clip_name, t2.grabindex, t2.dump_name, {agg_columns}
    FROM 
    (SELECT clip_name, grabindex, dump_name, {label_columns} FROM {main_data} UNION ALL SELECT clip_name, grabindex, dump_name, {label_columns} FROM {secondary_data}) t2
    INNER JOIN t1 
    ON t1.clip_name = t2.clip_name AND t1.grabindex = t2.grabindex
    GROUP BY t2.clip_name, t2.grabindex, t2.dump_name
"""

IMG_LIMIT = 25
