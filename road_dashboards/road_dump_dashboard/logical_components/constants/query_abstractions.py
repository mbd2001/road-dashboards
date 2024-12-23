from functools import reduce
from operator import mul

from pypika import Criterion, EmptyCriterion, Query, Tuple
from pypika.queries import QueryBuilder, Selectable
from pypika.terms import Term

from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
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
