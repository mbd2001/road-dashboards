from functools import partial
from typing import Callable

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, no_update
from pypika import Criterion, EmptyCriterion
from pypika.queries import QueryBuilder, Selectable
from pypika.terms import Term

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.init_data_sources import EXISTING_TABLES
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import (
    base_data_subquery,
    diff_terms_subquery,
    ids_query_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_with_dropdown import (
    ConfMatGraphWithDropdown,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.data_filters import DataFilters
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import (
    df_to_jump,
    dump_object,
    execute,
    load_object,
)
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class JumpModal(GridObject):
    LINES_LIMIT = 4096
    DIFF_TOLERANCE = 8

    def __init__(
        self,
        page_filters_id: str,
        triggering_conf_mats: list[ConfMatGraph] = None,
        triggering_dropdown_conf_mats: list[ConfMatGraphWithDropdown] = None,
        triggering_filters: list[DataFilters] = None,
        component_id: str = "",
    ):
        self.page_filters_id = page_filters_id
        self.triggering_conf_mats = triggering_conf_mats if triggering_conf_mats else []
        self.triggering_dropdown_conf_mats = triggering_dropdown_conf_mats if triggering_dropdown_conf_mats else []
        self.triggering_filters = triggering_filters if triggering_filters else []
        super().__init__(full_grid_row=True, component_id=component_id)

    def _generate_ids(self):
        self.extra_columns_dropdown_id = self._generate_id("extra_columns_dropdown")
        self.diff_tolerance_input_id = self._generate_id("diff_tolerance_input")
        self.generate_jump_btn_id = self._generate_id("generate_jump_btn")
        self.download_jump_id = self._generate_id("download_jump")
        self.curr_query_id = self._generate_id("curr_query")

    def layout(self):
        jump_layout = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Jump Properties"), close_button=False),
                dbc.ModalBody(
                    [
                        dcc.Store(id=self.curr_query_id),
                        dcc.Download(id=self.download_jump_id),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Dropdown(
                                        id=self.extra_columns_dropdown_id,
                                        multi=True,
                                        clearable=True,
                                        placeholder="Extra columns to export",
                                        value=None,
                                    )
                                ),
                                dbc.Col(
                                    dcc.Input(
                                        id=self.diff_tolerance_input_id,
                                        style={"minWidth": "100%"},
                                        placeholder=f"Sequence if gis diff smaller than (default {self.DIFF_TOLERANCE}):",
                                        type="number",
                                    )
                                ),
                            ],
                        ),
                        dbc.Button("Save Jump File", id=self.generate_jump_btn_id, color="primary", className="mt-3"),
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
                State(self.page_filters_id, "data"),
                prevent_initial_call=True,
            )
            def generic_diff_jump_file(
                n_clicks, main_dump, secondary_dump, filter_ignores, main_tables, md_tables, page_filters
            ):
                if not n_clicks or not main_tables:
                    return no_update, no_update, no_update

                main_tables: list[Base] = load_object(main_tables)
                md_tables: list[Base] = load_object(md_tables) if md_tables else None
                page_filters: Criterion = load_object(page_filters)

                partial_query = partial(
                    diff_terms_subquery,
                    main_tables=[table for table in main_tables if table.dataset_name == main_dump],
                    secondary_tables=[table for table in main_tables if table.dataset_name == secondary_dump],
                    main_md=[table for table in md_tables if table.dataset_name == main_dump],
                    secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                    diff_column=conf_mat.column,
                    data_filter=conf_mat.filter if filter_ignores else EmptyCriterion(),
                    page_filters=page_filters,
                )
                extra_columns = DataFilters.get_united_columns_dict(conf_mat.main_table, META_DATA)
                return dump_object(partial_query), True, extra_columns

        for dropdown_conf_mat in self.triggering_dropdown_conf_mats:

            @callback(
                Output(self.curr_query_id, "data", allow_duplicate=True),
                Output(self.component_id, "is_open", allow_duplicate=True),
                Output(self.extra_columns_dropdown_id, "options", allow_duplicate=True),
                Input(dropdown_conf_mat.generate_jump_btn_id, "n_clicks"),
                State(dropdown_conf_mat.main_dataset_dropdown_id, "value"),
                State(dropdown_conf_mat.secondary_dataset_dropdown_id, "value"),
                State(dropdown_conf_mat.main_table, "data"),
                State(META_DATA, "data"),
                State(self.page_filters_id, "data"),
                State(dropdown_conf_mat.columns_dropdown_id, "value"),
                prevent_initial_call=True,
            )
            def dynamic_diff_jump_file(
                n_clicks, main_dump, secondary_dump, main_tables, md_tables, page_filters, column
            ):
                if not n_clicks or not main_tables:
                    return no_update, no_update, no_update

                main_tables: list[Base] = load_object(main_tables)
                md_tables: list[Base] = load_object(md_tables) if md_tables else None
                page_filters: Criterion = load_object(page_filters)
                column: Column = getattr(EXISTING_TABLES[dropdown_conf_mat.main_table], column, None)

                partial_query = partial(
                    diff_terms_subquery,
                    main_tables=[table for table in main_tables if table.dataset_name == main_dump],
                    secondary_tables=[table for table in main_tables if table.dataset_name == secondary_dump],
                    main_md=[table for table in md_tables if table.dataset_name == main_dump],
                    secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                    diff_column=column,
                    page_filters=page_filters,
                )
                extra_columns = DataFilters.get_united_columns_dict(dropdown_conf_mat.main_table, META_DATA)
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
                md_tables: list[Base] = load_object(md_tables) if md_tables else None
                page_filters: Criterion = load_object(page_filters)

                partial_query = partial(
                    base_data_subquery,
                    main_tables=main_tables,
                    meta_data_tables=md_tables,
                    intersection_on=True,
                    page_filters=page_filters,
                )
                extra_columns = DataFilters.get_united_columns_dict(triggering_filter.main_table, META_DATA)
                return dump_object(partial_query), True, extra_columns

        @callback(
            Output(self.download_jump_id, "data"),
            Input(self.generate_jump_btn_id, "n_clicks"),
            State(self.curr_query_id, "data"),
            State(self.diff_tolerance_input_id, "value"),
            State(self.extra_columns_dropdown_id, "value"),
            State(self.page_filters_id, "data"),
        )
        def generate_jump(n_clicks, curr_query, diff_tolerance, extra_terms, page_filters):
            if not n_clicks or not curr_query:
                return no_update

            extra_terms = extra_terms if extra_terms is not None else []
            extra_terms = [Column(term) for term in extra_terms]
            page_filters: Criterion = load_object(page_filters)
            terms: list[Term] = [
                term for term in {MetaData.clip_name, MetaData.grabindex, *page_filters.find_(Column), *extra_terms}
            ]
            query_partial_func: Callable = load_object(curr_query)
            subquery: Selectable = query_partial_func(terms=terms)
            updated_terms = (
                [Column(name=term.alias or term.name) for term in subquery._selects]
                if isinstance(subquery, QueryBuilder)
                else terms
            )
            diff_tolerance = diff_tolerance if diff_tolerance is not None else self.DIFF_TOLERANCE
            query = ids_query_wrapper(
                sub_query=subquery,
                terms=updated_terms,
                limit=self.LINES_LIMIT,
                diff_tolerance=diff_tolerance,
            )
            jump_frames = execute(query)
            if jump_frames.empty:
                return no_update

            jump_name = "tmp_name"
            return dict(content=df_to_jump(jump_frames), filename=f"{jump_name}.jump")
