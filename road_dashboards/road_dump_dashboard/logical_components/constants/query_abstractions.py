from functools import reduce
from operator import mul

from pypika import Criterion, EmptyCriterion, Query, Tuple, functions
from pypika import analytics as an
from pypika.enums import SqlTypes
from pypika.queries import QueryBuilder
from pypika.terms import Case, Term

from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import Arbitrary
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


def base_data_subquery(
    main_tables: list[Base],
    meta_data_tables: list[Base],
    terms: list[Term],
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
    intersection_on: bool = False,
    limit: int | None = None,
) -> QueryBuilder:
    intersection_filter = get_intersection_filter(meta_data_tables, intersection_on)
    filters = Criterion.all([data_filter, page_filters, intersection_filter])
    joint_tables = [
        join_main_and_md(main_table, md_table)
        .select(*resolve_unambiguous(md_table, terms))
        .where(*resolve_unambiguous(md_table, [filters]))
        .orderby(md_table.dump_name, md_table.clip_name, md_table.grabindex)
        .limit(limit)
        for main_table, md_table in zip(main_tables, meta_data_tables)
    ]
    union_table = union_all_query_list(joint_tables)
    return union_table


def resolve_unambiguous(md_table: Base, terms: list[Term]) -> list[Term]:
    return [term.replace_table(current_table=None, new_table=md_table) for term in terms]


def get_intersection_filter(meta_data_tables: list[Base], intersection_on: bool):
    if not intersection_on or len(meta_data_tables) == 1:
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
        final_query = final_query.intersect(curr_query)

    return final_query


def get_main_secondary_subqueries(
    main_tables: list[Base],
    main_md: list[Base],
    secondary_tables: list[Base],
    secondary_md: list[Base],
    terms: list[Term],
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
):
    main_subquery = base_data_subquery(
        main_tables=main_tables,
        meta_data_tables=main_md,
        terms=terms,
        data_filter=data_filter,
        page_filters=page_filters,
    )
    secondary_subquery = base_data_subquery(
        main_tables=secondary_tables,
        meta_data_tables=secondary_md,
        terms=terms,
        data_filter=data_filter,
        page_filters=page_filters,
    )
    return main_subquery, secondary_subquery


def conf_mat_subquery(
    main_labels: list[Base],
    secondary_labels: list[Base],
    main_md: list[Base],
    secondary_md: list[Base],
    group_by_column: Column,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
):
    terms = list({group_by_column, MetaData.clip_name, MetaData.grabindex, MetaData.obj_id})
    main_subquery, secondary_subquery = get_main_secondary_subqueries(
        main_tables=main_labels,
        main_md=main_md,
        secondary_tables=secondary_labels,
        secondary_md=secondary_md,
        terms=terms,
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
    return Query.from_(sub_query).select(*partition_columns, *[term.alias for term in terms], percentage_calc)


def ids_query(
    main_tables: list[Base],
    main_md: list[Base],
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
    limit: int | None = None,
    diff_tolerance: int = 128,
):
    terms = list({MetaData.clip_name, MetaData.grabindex})
    main_subquery = base_data_subquery(
        main_tables=main_tables,
        meta_data_tables=main_md,
        terms=terms,
        data_filter=data_filter,
        intersection_on=True,
        page_filters=page_filters,
    )
    unique_ind_query = (
        Query.from_(main_subquery)
        .select(*[Arbitrary(term, alias=term.alias) for term in terms])
        .groupby(main_subquery.clip_name, main_subquery.grabindex)
    )
    group_cases = Query.from_(unique_ind_query).select(
        *terms,
        Case(alias="is_new_group")
        .when(
            (
                unique_ind_query.grabindex
                - an.Lag(unique_ind_query.grabindex)
                .over()
                .orderby(unique_ind_query.clip_name, unique_ind_query.grabindex)
            )
            >= diff_tolerance,
            1,
        )
        .else_(0),
    )
    sum_groups = Query.from_(group_cases).select(
        *terms,
        an.Sum(group_cases.is_new_group).orderby(group_cases.clip_name, group_cases.grabindex).as_("group_id"),
    )
    final_query = (
        Query.from_(sum_groups)
        .select(
            functions.Cast(functions.Min(sum_groups.grabindex), SqlTypes.INTEGER).as_("startframe"),
            functions.Cast(functions.Max(sum_groups.grabindex), SqlTypes.INTEGER).as_("endframe"),
            *[Arbitrary(term, alias=term.alias) for term in terms],
        )
        .groupby(sum_groups.clip_name, sum_groups.group_id)
        .limit(limit)
    )
    return final_query


def diff_ids_subquery(
    main_tables: list[Base],
    secondary_tables: list[Base],
    main_md: list[Base],
    secondary_md: list[Base],
    diff_column: Column,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
    limit: int | None = None,
):
    terms = list({diff_column, MetaData.clip_name, MetaData.grabindex, MetaData.obj_id})
    main_subquery, secondary_subquery = get_main_secondary_subqueries(
        main_tables=main_tables,
        main_md=main_md,
        secondary_tables=secondary_tables,
        secondary_md=secondary_md,
        terms=terms,
        data_filter=data_filter,
        page_filters=page_filters,
    )
    first_diff_col = diff_column.replace_table(None, main_subquery)
    second_diff_col = diff_column.replace_table(None, secondary_subquery)
    query = (
        Query.from_(main_subquery)
        .inner_join(secondary_subquery)
        .on(
            (main_subquery.clip_name == secondary_subquery.clip_name)
            & (main_subquery.grabindex == secondary_subquery.grabindex)
            & (main_subquery.obj_id == secondary_subquery.obj_id)
        )
        .select(main_subquery.clip_name, main_subquery.grabindex)
        .where(first_diff_col != second_diff_col)
        .distinct()
        .limit(limit)
    )
    return query


def diff_labels_subquery(
    main_tables: list[Base],
    secondary_tables: list[Base],
    main_md: list[Base],
    secondary_md: list[Base],
    label_columns: list[Term],
    diff_column: Column,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
    limit: int | None = None,
):
    ids_subquery = diff_ids_subquery(
        main_tables=main_tables,
        secondary_tables=secondary_tables,
        main_md=main_md,
        secondary_md=secondary_md,
        diff_column=diff_column,
        data_filter=data_filter,
        page_filters=page_filters,
        limit=limit,
    )

    terms = list({*label_columns})
    main_subquery, secondary_subquery = get_main_secondary_subqueries(
        main_tables=main_tables,
        main_md=main_md,
        secondary_tables=secondary_tables,
        secondary_md=secondary_md,
        terms=terms,
        data_filter=data_filter,
        page_filters=page_filters,
    )
    union_query = main_subquery.union_all(secondary_subquery)
    labels_query = (
        Query.from_(union_query).where(Tuple(MetaData.clip_name, MetaData.grabindex).isin(ids_subquery)).select(*terms)
    )
    return labels_query
