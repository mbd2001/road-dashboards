from functools import partial
from typing import Callable

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, no_update
from pypika import Criterion, EmptyCriterion, Query, functions
from pypika import analytics as an
from pypika.enums import SqlTypes
from pypika.queries import QueryBuilder, Selectable
from pypika.terms import Case, Term

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import loading_wrapper
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import (
    base_data_subquery,
    diff_terms_subquery,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.data_filters import DataFilters
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import (
    Arbitrary,
    df_to_jump,
    dump_object,
    execute,
    load_object,
    optional_inputs,
)
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class JumpModal(GridObject):
    LINES_LIMIT: int = 4096
    DIFF_TOLERANCE: int = 32

    def __init__(
        self,
        page_filters_id: str = "",
        triggering_conf_mats: list[ConfMatGraph] | None = None,
        triggering_filters: list[DataFilters] | None = None,
        component_id: str = "",
    ):
        self.page_filters_id = page_filters_id
        self.triggering_conf_mats = triggering_conf_mats if triggering_conf_mats else []
        self.triggering_filters = triggering_filters if triggering_filters else []
        super().__init__(full_grid_row=True, component_id=component_id)

    def _generate_ids(self):
        self.extra_columns_dropdown_id = self._generate_id("extra_columns_dropdown")
        self.diff_tolerance_input_id = self._generate_id("diff_tolerance_input")
        self.limit_input_id = self._generate_id("limit_input")
        self.generate_jump_btn_id = self._generate_id("generate_jump_btn")
        self.download_jump_id = self._generate_id("download_jump")
        self.curr_query_id = self._generate_id("curr_query")
        self.jump_name_input_id = self._generate_id("jump_name_input")

    def layout(self):
        jump_layout = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Jump Properties"), close_button=False),
                dbc.ModalBody(
                    [
                        dcc.Store(id=self.curr_query_id),
                        dbc.Row(
                            dbc.Col(
                                dcc.Dropdown(
                                    id=self.extra_columns_dropdown_id,
                                    multi=True,
                                    clearable=True,
                                    placeholder="Extra columns to export",
                                    value=None,
                                ),
                                width=12,  # Ensure consistent left and right margins
                            ),
                            className="mb-3",
                        ),
                        dbc.Row(
                            dbc.Col(
                                dcc.Input(
                                    id=self.jump_name_input_id,
                                    style={"minWidth": "100%"},
                                    placeholder="Enter jump file name (default tmp_name.jump):",
                                    type="text",
                                ),
                                width=12,  # Ensure consistent left and right margins
                            ),
                            className="mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Input(
                                        id=self.diff_tolerance_input_id,
                                        style={"minWidth": "100%"},
                                        placeholder=f"Merge diffs smaller than (default {self.DIFF_TOLERANCE}):",
                                        type="number",
                                    )
                                ),
                                dbc.Col(
                                    dcc.Input(
                                        id=self.limit_input_id,
                                        style={"minWidth": "100%"},
                                        placeholder=f"Max lines in jump file (default {self.LINES_LIMIT}):",
                                        type="number",
                                    )
                                ),
                            ],
                            className="mt-3",
                        ),
                        dbc.Button("Save Jump File", id=self.generate_jump_btn_id, color="primary", className="mt-3"),
                        loading_wrapper(dcc.Download(id=self.download_jump_id)),
                    ]
                ),
            ],
            id=self.component_id,
            is_open=False,
            centered=True,
            size="lg",
        )
        return jump_layout

    def _callbacks(self):
        for conf_mat in self.triggering_conf_mats:

            @callback(
                Output(self.curr_query_id, "data", allow_duplicate=True),
                Output(self.component_id, "is_open", allow_duplicate=True),
                Output(self.extra_columns_dropdown_id, "options", allow_duplicate=True),
                Input(conf_mat.generate_jump_btn_id, "n_clicks"),
                State(conf_mat.main_dataset_dropdown_id, "value"),
                State(conf_mat.secondary_dataset_dropdown_id, "value"),
                State(conf_mat.filter_ignores_btn_id, "on"),
                State(conf_mat.main_table, "data"),
                State(META_DATA, "data"),
                optional_inputs(
                    page_filters=State(conf_mat.page_filters_id, "data"),
                    column=State(conf_mat.columns_dropdown_id, "value"),
                ),
                prevent_initial_call=True,
            )
            def generic_diff_jump_file(
                n_clicks,
                main_dump,
                secondary_dump,
                filter_ignores,
                main_tables,
                md_tables,
                optional,
                column=conf_mat.column,
                filter=conf_mat.filter,
            ):
                if not n_clicks or not main_tables:
                    return no_update, no_update, no_update

                main_tables: list[Base] = load_object(main_tables)
                column: Term = column or getattr(type(main_tables[0]), optional["column"], None)
                if not column:
                    return no_update

                md_tables: list[Base] = load_object(md_tables)
                page_filters: str = optional.get("page_filters", None)
                page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()

                partial_query = partial(
                    diff_terms_subquery,
                    main_tables=[table for table in main_tables if table.dataset_name == main_dump],
                    secondary_tables=[table for table in main_tables if table.dataset_name == secondary_dump],
                    main_md=[table for table in md_tables if table.dataset_name == main_dump],
                    secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                    diff_column=column,
                    data_filter=filter if filter_ignores else EmptyCriterion(),
                    page_filters=page_filters,
                )
                extra_columns = DataFilters.get_united_columns_dict(type(main_tables[0]))
                return dump_object(partial_query), True, extra_columns

        for triggering_filter in self.triggering_filters:

            @callback(
                Output(self.curr_query_id, "data", allow_duplicate=True),
                Output(self.component_id, "is_open", allow_duplicate=True),
                Output(self.extra_columns_dropdown_id, "options", allow_duplicate=True),
                Input(triggering_filter.generate_jump_btn_id, "n_clicks"),
                State(triggering_filter.main_table, "data"),
                State(META_DATA, "data"),
                State(self.page_filters_id, "data"),
                prevent_initial_call=True,
            )
            def dataset_jump_file(n_clicks, main_tables, md_tables, page_filters):
                if not n_clicks or not main_tables:
                    return no_update, no_update, no_update

                main_tables: list[Base] = load_object(main_tables)
                md_tables: list[Base] = load_object(md_tables)
                page_filters: Criterion = load_object(page_filters)

                partial_query = partial(
                    base_data_subquery,
                    main_tables=main_tables,
                    meta_data_tables=md_tables,
                    intersection_on=True,
                    page_filters=page_filters,
                )
                extra_columns = DataFilters.get_united_columns_dict(type(main_tables[0]))
                return dump_object(partial_query), True, extra_columns

        @callback(
            Output(self.download_jump_id, "data"),
            Input(self.generate_jump_btn_id, "n_clicks"),
            State(self.curr_query_id, "data"),
            State(self.diff_tolerance_input_id, "value"),
            State(self.limit_input_id, "value"),
            State(self.extra_columns_dropdown_id, "value"),
            State(self.page_filters_id, "data"),
            State(self.jump_name_input_id, "value"),
        )
        def generate_jump(n_clicks, curr_query, diff_tolerance, lines_limit, extra_terms, page_filters, jump_name):
            if not n_clicks or not curr_query:
                return no_update

            extra_terms = extra_terms if extra_terms is not None else []
            extra_terms = [Column(term, str) for term in extra_terms]
            page_filters: Criterion = load_object(page_filters)
            terms: list[Term] = [
                term for term in {MetaData.clip_name, MetaData.grabindex, *page_filters.find_(Column), *extra_terms}
            ]
            query_partial_func: Callable = load_object(curr_query)
            subquery: Selectable = query_partial_func(terms=terms)
            updated_terms = (
                [Column(term.alias or term.name, str) for term in subquery._selects]
                if isinstance(subquery, QueryBuilder)
                else terms
            )
            diff_tolerance = diff_tolerance if diff_tolerance is not None else self.DIFF_TOLERANCE
            lines_limit = lines_limit if lines_limit is not None else self.LINES_LIMIT
            query = self.group_frames_with_gi_below_diff_query_wrapper(
                sub_query=subquery,
                terms=updated_terms,
                limit=lines_limit,
                diff_tolerance=diff_tolerance,
            )
            jump_frames = execute(query)
            if jump_frames.empty:
                return no_update

            jump_name = jump_name if jump_name else "tmp_name"
            return dict(content=df_to_jump(jump_frames), filename=f"{jump_name}.jump")

    @staticmethod
    def group_frames_with_gi_below_diff_query_wrapper(
        sub_query: Selectable,
        terms: list[Term],
        limit: int | None = None,
        diff_tolerance: int = 0,
    ) -> QueryBuilder:
        unique_frames_query = JumpModal.select_unique_frames(sub_query, terms)
        group_ids_query = JumpModal.add_groups_ids_based_on_diff(unique_frames_query, terms, diff_tolerance)
        final_query = JumpModal.select_one_term_per_group(group_ids_query, terms, limit)
        return final_query

    @staticmethod
    def select_unique_frames(base_data_query: Selectable, terms: list[Term]) -> QueryBuilder:
        query = (
            Query.from_(base_data_query)
            .select(*[Arbitrary(term, alias=term.alias) for term in terms])
            .groupby(base_data_query.clip_name, base_data_query.grabindex)
        )
        return query

    @staticmethod
    def add_groups_ids_based_on_diff(
        unique_frames_query: QueryBuilder, terms: list[Term], diff_tolerance: int
    ) -> QueryBuilder:
        new_groups_query = Query.from_(unique_frames_query).select(
            *terms,
            Case(alias="is_new_group")
            .when(
                (
                    unique_frames_query.grabindex
                    - an.Lag(unique_frames_query.grabindex)
                    .over()
                    .orderby(unique_frames_query.clip_name, unique_frames_query.grabindex)
                )
                > diff_tolerance,
                1,
            )
            .else_(0),
        )
        cum_sum_groups_query = Query.from_(new_groups_query).select(
            *terms,
            an.Sum(new_groups_query.is_new_group)
            .orderby(new_groups_query.clip_name, new_groups_query.grabindex)
            .as_("group_id"),
        )
        return cum_sum_groups_query

    @staticmethod
    def select_one_term_per_group(
        sum_groups_query: QueryBuilder, terms: list[Term], limit: int | None = None
    ) -> QueryBuilder:
        final_query = (
            Query.from_(sum_groups_query)
            .select(
                MetaData.clip_name,
                functions.Cast(functions.Min(sum_groups_query.grabindex), SqlTypes.INTEGER).as_("startframe"),
                functions.Cast(functions.Max(sum_groups_query.grabindex), SqlTypes.INTEGER).as_("endframe"),
                functions.Cast(
                    functions.Max(sum_groups_query.grabindex) - functions.Min(sum_groups_query.grabindex) + 1,
                    SqlTypes.INTEGER,
                ).as_("event_length"),
                *[
                    Arbitrary(term, alias=term.alias)
                    for term in terms
                    if term.alias not in ["clip_name", "grabindex", "obj_id"]
                ],
            )
            .groupby(sum_groups_query.clip_name, sum_groups_query.group_id)
            .limit(limit)
        )
        return final_query
