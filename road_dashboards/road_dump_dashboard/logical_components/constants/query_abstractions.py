from functools import reduce
from operator import mul

from pypika import Criterion, EmptyCriterion, Query, Tuple
from pypika import analytics as an
from pypika import functions
from pypika.queries import QueryBuilder
from pypika.terms import Term

from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


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
    group_by_column: Column,
    main_labels: list[Base],
    secondary_labels: list[Base],
    main_md: list[Base] = None,
    secondary_md: list[Base] = None,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
):
    terms = list({group_by_column, MetaData.clip_name, MetaData.grabindex, MetaData.obj_id})
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
    first_diff_col = group_by_column.replace_table(None, main_subquery)
    second_diff_col = group_by_column.replace_table(None, secondary_subquery)
    group_by_query = (
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
    return group_by_query


def percentage_wrapper(
    sub_query: QueryBuilder,
    percentage_column: Column,
    partition_columns: list[Column],
    terms: list[Term],
):
    percentage_calc = (percentage_column * 100.0 / an.Sum(percentage_column).over(*partition_columns)).as_("percentage")
    return Query.from_(sub_query).select(*partition_columns, *[term for term in terms], percentage_calc)


def diff_ids_subquery(
    diff_column: Column,
    main_labels: list[Base],
    secondary_labels: list[Base],
    main_md: list[Base] = None,
    secondary_md: list[Base] = None,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
    limit: int | None = None,
):
    terms = list({diff_column, MetaData.clip_name, MetaData.grabindex, MetaData.obj_id})
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
    diff_query = (
        Query.from_(main_subquery)
        .inner_join(secondary_subquery)
        .on(
            (main_subquery.clip_name == secondary_subquery.clip_name)
            & (main_subquery.grabindex == secondary_subquery.grabindex)
            & (main_subquery.obj_id == secondary_subquery.obj_id)
        )
        .where(first_diff_col != second_diff_col)
        .select(main_subquery.clip_name, main_subquery.grabindex)
        .distinct()
        .limit(limit)
    )
    return diff_query


def diff_labels_subquery(
    diff_column: Column,
    label_columns: list[Term],
    main_labels: list[Base],
    secondary_labels: list[Base],
    main_md: list[Base] = None,
    secondary_md: list[Base] = None,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
    limit: int | None = None,
):
    diff_ids = diff_ids_subquery(
        diff_column,
        main_labels,
        secondary_labels,
        main_md,
        secondary_md,
        data_filter,
        page_filters,
        limit,
    )

    terms = list({*label_columns})
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

    union_query = main_subquery.union_all(secondary_subquery)
    labels_query = (
        Query.from_(union_query)
        .where(Tuple(MetaData.clip_name, MetaData.grabindex).isin(diff_ids))
        .select(*terms)
        .orderby(MetaData.dump_name, MetaData.clip_name, MetaData.grabindex)
    )
    return labels_query
