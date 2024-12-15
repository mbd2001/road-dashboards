from functools import reduce
from operator import mul

from pypika import Criterion, EmptyCriterion, Query, Tuple, functions
from pypika import analytics as an
from pypika.enums import SqlTypes
from pypika.queries import QueryBuilder, Selectable
from pypika.terms import Case, Term

from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import Arbitrary, get_main_and_secondary_columns
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


def base_data_subquery(
    main_tables: list[Base],
    meta_data_tables: list[Base],
    terms: list[Term],
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
    intersection_on: bool = False,
    to_order: bool = True,
) -> Selectable:
    intersection_filter = get_intersection_filter(meta_data_tables, intersection_on)
    filters = Criterion.all([data_filter, page_filters, intersection_filter])
    joint_tables = [
        join_main_and_md(main_table, md_table)
        .select(*resolve_unambiguous(main_table, terms))
        .where(*resolve_unambiguous(main_table, [filters]))
        .orderby(*[md_table.dump_name] if to_order else [])
        for main_table, md_table in zip(main_tables, meta_data_tables)
    ]
    union_table = union_all_query_list(joint_tables)
    return union_table


def resolve_unambiguous(main_table: Base, terms: list[Term]) -> list[Term]:
    return [term.replace_table(current_table=None, new_table=main_table) for term in terms]


def get_intersection_filter(meta_data_tables: list[Base], intersection_on: bool) -> Criterion:
    if not intersection_on or len(meta_data_tables) == 1:
        return EmptyCriterion()

    return Tuple(MetaData.clip_name, MetaData.grabindex).isin(
        intersect_query_list(
            [Query.from_(md_table).select(md_table.clip_name, md_table.grabindex) for md_table in meta_data_tables]
        )
    )


def join_main_and_md(main_table: Base, md_table: Base) -> QueryBuilder:
    if not md_table or (md_table == main_table):
        return Query.from_(main_table)

    return (
        Query.from_(main_table)
        .inner_join(md_table)
        .on((main_table.clip_name == md_table.clip_name) & (main_table.grabindex == md_table.grabindex))
    )


def union_all_query_list(query_list: list[Selectable]) -> Selectable:
    ret = reduce(mul, query_list)
    return ret


def intersect_query_list(query_list: list[QueryBuilder]) -> QueryBuilder:
    queries_iter = iter(query_list)
    final_query = next(queries_iter)
    while curr_query := next(queries_iter, None):
        final_query = final_query.intersect(curr_query)

    return final_query


def join_on_obj_id(
    main_tables: list[Base],
    secondary_tables: list[Base],
    main_md: list[Base],
    secondary_md: list[Base],
    terms: list[Term] | None = None,
    diff_terms: list[Term] | None = None,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
) -> tuple[Selectable, Selectable, Selectable]:
    diff_terms = diff_terms if diff_terms is not None else []
    terms = terms if terms is not None else []
    terms = list({MetaData.clip_name, MetaData.grabindex, MetaData.obj_id, *terms})

    base_terms = list({*terms, *diff_terms})
    main_subquery, secondary_subquery = [
        base_data_subquery(
            main_tables=main_table,
            meta_data_tables=md_table,
            terms=base_terms,
            data_filter=data_filter,
            page_filters=page_filters,
            to_order=False,
        )
        for main_table, md_table in [[main_tables, main_md], [secondary_tables, secondary_md]]
    ]
    updated_terms = (
        [Column(term.alias, str, alias=term.alias, table=main_subquery) for term in terms]
        + [Column(term.alias, str, alias=f"main_{term.alias}", table=main_subquery) for term in diff_terms]
        + [Column(term.alias, str, alias=f"secondary_{term.alias}", table=secondary_subquery) for term in diff_terms]
    )
    join_query = (
        Query.from_(main_subquery)
        .inner_join(secondary_subquery)
        .on(
            (main_subquery.clip_name == secondary_subquery.clip_name)
            & (main_subquery.grabindex == secondary_subquery.grabindex)
            & (main_subquery.obj_id == secondary_subquery.obj_id)
        )
        .select(*updated_terms)
    )
    return join_query, main_subquery, secondary_subquery


def conf_mat_subquery(
    main_labels: list[Base],
    secondary_labels: list[Base],
    main_md: list[Base],
    secondary_md: list[Base],
    group_by_column: Term,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
) -> QueryBuilder:
    join_query, _, _ = join_on_obj_id(
        main_tables=main_labels,
        main_md=main_md,
        secondary_tables=secondary_labels,
        secondary_md=secondary_md,
        diff_terms=[group_by_column],
        data_filter=data_filter,
        page_filters=page_filters,
    )
    first_group_by_column, second_group_by_column = get_main_and_secondary_columns(group_by_column)
    group_by_query = (
        Query.from_(join_query)
        .groupby(first_group_by_column, second_group_by_column)
        .select(first_group_by_column, second_group_by_column, functions.Count("*", "overall"))
    )
    return group_by_query


def percentage_wrapper(
    sub_query: Selectable,
    percentage_column: Term,
    partition_columns: list[Term],
    terms: list[Term],
) -> QueryBuilder:
    percentage_calc = (percentage_column * 100.0 / an.Sum(percentage_column).over(*partition_columns)).as_("percentage")
    return Query.from_(sub_query).select(*partition_columns, *[term.alias for term in terms], percentage_calc)


def ids_query_wrapper(
    sub_query: Selectable,
    terms: list[Term],
    limit: int | None = None,
    diff_tolerance: int = 0,
) -> QueryBuilder:
    unique_ind_query = (
        Query.from_(sub_query)
        .select(*[Arbitrary(term, alias=term.alias) for term in terms])
        .groupby(sub_query.clip_name, sub_query.grabindex)
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
            > diff_tolerance,
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
            MetaData.clip_name,
            functions.Cast(functions.Min(sum_groups.grabindex), SqlTypes.INTEGER).as_("startframe"),
            functions.Cast(functions.Max(sum_groups.grabindex), SqlTypes.INTEGER).as_("endframe"),
            functions.Cast(
                functions.Max(sum_groups.grabindex) - functions.Min(sum_groups.grabindex) + 1, SqlTypes.INTEGER
            ).as_("event_length"),
            *[
                Arbitrary(term, alias=term.alias)
                for term in terms
                if term.alias not in ["clip_name", "grabindex", "obj_id"]
            ],
        )
        .groupby(sum_groups.clip_name, sum_groups.group_id)
        .limit(limit)
    )
    return final_query


def diff_terms_subquery(
    main_tables: list[Base],
    secondary_tables: list[Base],
    main_md: list[Base],
    secondary_md: list[Base],
    diff_column: Term,
    terms: list[Term] | None = None,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
) -> QueryBuilder:
    if terms is None:
        terms = []

    join_query, main_subquery, secondary_subquery = join_on_obj_id(
        main_tables=main_tables,
        main_md=main_md,
        secondary_tables=secondary_tables,
        secondary_md=secondary_md,
        terms=terms,
        diff_terms=[diff_column],
        data_filter=data_filter,
        page_filters=page_filters,
    )
    first_diff_col = Column(diff_column.alias, str, table=main_subquery)
    second_diff_col = Column(diff_column.alias, str, table=secondary_subquery)
    query = join_query.where(first_diff_col != second_diff_col)
    return query


def diff_labels_subquery(
    main_tables: list[Base],
    secondary_tables: list[Base],
    main_md: list[Base],
    secondary_md: list[Base],
    label_columns: list[Term],
    diff_column: Term,
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
    limit: int | None = None,
) -> QueryBuilder:
    diff_terms = diff_terms_subquery(
        main_tables=main_tables,
        secondary_tables=secondary_tables,
        main_md=main_md,
        secondary_md=secondary_md,
        diff_column=diff_column,
        data_filter=data_filter,
        page_filters=page_filters,
    )
    ids_subquery = Query.from_(diff_terms).select(diff_terms.clip_name, diff_terms.grabindex).distinct().limit(limit)

    terms = list({*label_columns})
    labels_queries = [
        base_data_subquery(
            main_tables=main_table,
            meta_data_tables=md_table,
            terms=terms,
            data_filter=data_filter,
            page_filters=page_filters,
        )
        for main_table, md_table in [[main_tables, main_md], [secondary_tables, secondary_md]]
    ]
    union_query = union_all_query_list(labels_queries)
    labels_query = (
        Query.from_(union_query).where(Tuple(MetaData.clip_name, MetaData.grabindex).isin(ids_subquery)).select(*terms)
    )
    return labels_query


def general_labels_subquery(
    main_tables: list[Base],
    meta_data_tables: list[Base],
    label_columns: list[Term],
    data_filter: Criterion = EmptyCriterion(),
    page_filters: Criterion = EmptyCriterion(),
    limit: int | None = None,
) -> QueryBuilder:
    ids_terms = [MetaData.clip_name, MetaData.grabindex]
    ids_query = base_data_subquery(
        main_tables=main_tables,
        meta_data_tables=meta_data_tables,
        terms=ids_terms,
        data_filter=data_filter,
        page_filters=page_filters,
        intersection_on=True,
    )
    ids_subquery = Query.from_(ids_query).select(ids_query.clip_name, ids_query.grabindex).distinct().limit(limit)

    terms = list({*label_columns})
    labels_query = base_data_subquery(
        main_tables=main_tables,
        meta_data_tables=meta_data_tables,
        terms=terms,
        data_filter=data_filter,
        page_filters=page_filters,
        intersection_on=True,
    )
    final_query = (
        Query.from_(labels_query).where(Tuple(MetaData.clip_name, MetaData.grabindex).isin(ids_subquery)).select(*terms)
    )
    return final_query
