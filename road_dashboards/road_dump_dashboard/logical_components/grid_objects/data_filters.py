from __future__ import annotations

from typing import Callable

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, Patch, State, callback, callback_context, dcc, html, no_update
from pypika import Criterion, EmptyCriterion, Query

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.init_data_sources import EXISTING_TABLES
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import card_wrapper
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import base_data_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import dump_object, execute, load_object


class DataFilters(GridObject):
    MAX_FILTERS_PER_GROUP: int = 10

    def __init__(
        self,
        main_table: str,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.main_table = main_table
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.final_filter_id = self._generate_id("final_filter")

        self.subgroup_id = self._generate_id("subgroup")
        self.add_subgroup_btn_id = self._generate_id("add_subgroup_btn")
        self.remove_subgroup_btn_id = self._generate_id("remove_subgroup_btn")
        self.add_filter_btn_id = self._generate_id("add_filter_btn")
        self.subgroup_filters_id = self._generate_id("subgroup_filters")

        self.filter_id = self._generate_id("filter")
        self.remove_filter_btn_id = self._generate_id("remove_filter_btn")
        self.column_id = self._generate_id("column")
        self.operation_id = self._generate_id("operation")
        self.filter_val_obj_id = self._generate_id("filter_val_obj")
        self.filter_val_id = self._generate_id("filter_val")

        self.update_filters_btn_id = self._generate_id("update_filters_btn")
        self.show_n_frames_btn_id = self._generate_id("show_n_frames_btn")
        self.generate_jump_btn_id = self._generate_id("generate_jump_btn")

    def layout(self):
        empty_layout = card_wrapper(
            [
                dcc.Store(self.final_filter_id, data=dump_object(EmptyCriterion())),
                html.H3("Filters"),
                html.Div(
                    id=self.component_id,
                    children=[
                        self.get_group_layout(
                            1, self.get_united_columns_dict(self.main_table, META_DATA), self.MAX_FILTERS_PER_GROUP
                        )
                    ],
                ),
                dbc.Stack(
                    [
                        dbc.Button(
                            "Update Filters", id=self.update_filters_btn_id, color="success", style={"margin": "10px"}
                        ),
                        dbc.Button(
                            "Draw Frames", id=self.show_n_frames_btn_id, color="primary", style={"margin": "10px"}
                        ),
                        dbc.Button(
                            "Save Jump File", id=self.generate_jump_btn_id, color="primary", style={"margin": "10px"}
                        ),
                    ],
                    direction="horizontal",
                    gap=1,
                ),
            ]
        )
        return empty_layout

    def _callbacks(self):
        @callback(
            Output({"type": self.subgroup_filters_id, "index": MATCH}, "children"),
            Input({"type": self.add_filter_btn_id, "index": MATCH}, "n_clicks"),
            Input({"type": self.add_subgroup_btn_id, "index": MATCH}, "n_clicks"),
            State({"type": self.subgroup_filters_id, "index": MATCH}, "children"),
        )
        def add_filters(add_clicks, add_group, filters_list):
            if not any([add_clicks, add_group]) or not callback_context.triggered_id:
                return no_update

            patched_children = Patch()
            empty_index = None
            for ind in range(len(filters_list) - 1, -1, -1):
                single_filter = filters_list[ind]
                if single_filter["props"]["style"].get("display") == "none":
                    empty_index = single_filter["props"]["id"]["index"]
                    del patched_children[ind]

            if (not empty_index) and len(filters_list) < self.MAX_FILTERS_PER_GROUP:
                group_ind = callback_context.triggered_id["index"]
                base_ind = group_ind * self.MAX_FILTERS_PER_GROUP
                empty_index = self.get_empty_index(base_ind, filters_list, self.MAX_FILTERS_PER_GROUP)

            button_type = callback_context.triggered_id["type"]
            columns_options = self.get_united_columns_dict(self.main_table, META_DATA)
            if button_type == self.add_filter_btn_id and empty_index:
                patched_children.append(self.get_filter_row_initial_layout(empty_index, columns_options))
            elif button_type == self.add_subgroup_btn_id and empty_index:
                patched_children.append(self.get_group_layout(empty_index, columns_options, self.MAX_FILTERS_PER_GROUP))

            return patched_children

        @callback(
            Output({"type": self.filter_id, "index": MATCH}, "style"),
            Input({"type": self.remove_filter_btn_id, "index": MATCH}, "n_clicks"),
        )
        def remove_filter(remove_clicks):
            if not remove_clicks or not callback_context.triggered_id:
                return no_update

            patched_style = Patch()
            patched_style["display"] = "none"
            return patched_style

        @callback(
            Output({"type": self.subgroup_id, "index": MATCH}, "style"),
            Input({"type": self.remove_subgroup_btn_id, "index": MATCH}, "n_clicks"),
        )
        def remove_sub_group(remove_clicks):
            if not remove_clicks or not callback_context.triggered_id:
                return no_update

            if callback_context.triggered_id["index"] == 1:
                return no_update

            patched_style = Patch()
            patched_style["display"] = "none"
            return patched_style

        @callback(
            Output({"type": self.operation_id, "index": MATCH}, "options"),
            Output({"type": self.operation_id, "index": MATCH}, "value"),
            Input({"type": self.column_id, "index": MATCH}, "value"),
        )
        def update_operation_dropdown_options(column):
            if not column:
                return {}, ""

            if not callback_context.triggered_id:
                return no_update, no_update

            column: Column = self.get_column_from_tables(column, self.main_table, META_DATA)
            if column.type is str:
                options = {
                    "eq": "Equal",
                    "ne": "Not Equal",
                    "isnull": "Is NULL",
                    "isnotnull": "Is not NULL",
                    "like": "Like",
                    "isin": "In",
                    "notin": "Not In",
                }
            elif column.type is bool:
                options = {
                    "eq": "Equal",
                    "ne": "Not Equal",
                    "isnull": "Is NULL",
                    "isnotnull": "Is not NULL",
                }
            else:
                options = {
                    "gt": "Greater",
                    "gte": "Greater or equal",
                    "lt": "Less",
                    "lte": "Less or equal",
                    "eq": "Equal",
                    "ne": "Not Equal",
                    "isnull": "Is NULL",
                    "isnotnull": "Is not NULL",
                }
            return options, ""

        @callback(
            Output({"type": self.filter_val_obj_id, "index": MATCH}, "children"),
            Input({"type": self.operation_id, "index": MATCH}, "value"),
            State({"type": self.operation_id, "index": MATCH}, "id"),
            State({"type": self.column_id, "index": MATCH}, "value"),
            Input(self.main_table, "data"),
            Input(META_DATA, "data"),
        )
        def update_meta_data_values_options(operation, index, column, main_tables, md_tables):
            curr_index = index["index"]
            if not column or not operation:
                return dcc.Input(
                    id={"type": self.filter_val_id, "index": curr_index},
                    style={"minWidth": "100%", "display": "block"},
                    placeholder="----",
                    value=None,
                    type="text",
                )

            if not callback_context.triggered_id:
                return no_update

            column: Column = self.get_column_from_tables(column, self.main_table, META_DATA)
            if operation in ["isnull", "isnotnull"]:
                return dcc.Input(
                    id={"type": self.filter_val_id, "index": curr_index},
                    style={"minWidth": "100%", "display": "none"},
                    placeholder="----",
                    value=None,
                    type="text",
                )
            elif operation in ["eq", "ne", "isin", "notin"] and column.type in [str, bool]:
                multi = operation in ["isin", "notin"]
                if column.type is bool:
                    distinguish_values = {"T": "True", "": "False"}
                else:
                    main_tables: list[Base] = load_object(main_tables)
                    md_tables: list[Base] = load_object(md_tables) if md_tables else None
                    distinguish_values = self.get_distinct_string_values(column, main_tables, md_tables)

                return dcc.Dropdown(
                    id={"type": self.filter_val_id, "index": curr_index},
                    style={"minWidth": "100%", "display": "block"},
                    multi=multi,
                    clearable=True,
                    placeholder="----",
                    value=None,
                    options=distinguish_values,
                )
            else:
                input_type = "text" if column.type in [str, bool] else "number"
                return dcc.Input(
                    id={"type": self.filter_val_id, "index": curr_index},
                    style={"minWidth": "100%", "marginBottom": "10px", "display": "block"},
                    placeholder="----",
                    value=None,
                    type=input_type,
                )

        @callback(
            Output(self.final_filter_id, "data"),
            Input(self.update_filters_btn_id, "n_clicks"),
            State(self.component_id, "children"),
        )
        def generate_curr_filters(n_clicks, filters):
            if not filters:
                return dump_object(EmptyCriterion())

            first_group = filters[0]
            md_filters = self.recursive_build_meta_data_filters(first_group)
            return dump_object(md_filters)

    def get_group_layout(self, index: int, md_columns_options: list[str], max_filters_per_group: int):
        group_layout = dbc.Row(
            id={"type": self.subgroup_id, "index": index},
            children=[
                dbc.Stack(
                    children=[
                        daq.BooleanSwitch(
                            on=False,
                            label="And <-> Or",
                            labelPosition="top",
                        ),
                        dbc.Button(
                            className=f"ms-auto fas fa-plus",
                            id={"type": self.add_filter_btn_id, "index": index},
                            color="secondary",
                            style={"margin": "10px"},
                        ),
                        dbc.Button(
                            className=f"fas fa-link",
                            id={"type": self.add_subgroup_btn_id, "index": index},
                            color="secondary",
                            style={"margin": "10px"},
                        ),
                        dbc.Button(
                            className=f"fas fa-trash",
                            id={"type": self.remove_subgroup_btn_id, "index": index},
                            color="secondary",
                            style={"margin": "10px"},
                        ),
                    ],
                    direction="horizontal",
                    gap=1,
                ),
                html.Div(
                    id={"type": self.subgroup_filters_id, "index": index},
                    children=[self.get_filter_row_initial_layout(index * max_filters_per_group, md_columns_options)],
                ),
            ],
            style={"border": "2px lightskyblue solid", "border-radius": "20px", "margin": "20px"},
        )
        return group_layout

    def get_filter_row_initial_layout(self, index: int, md_columns_options: list[str]):
        single_filter_initial_layout = dbc.Row(
            id={"type": self.filter_id, "index": index},
            children=[
                dbc.Col(
                    children=dcc.Dropdown(
                        id={"type": self.column_id, "index": index},
                        style={"minWidth": "100%"},
                        multi=False,
                        clearable=True,
                        placeholder="Attribute",
                        value=None,
                        options=md_columns_options,
                    ),
                ),
                dbc.Col(
                    children=dcc.Dropdown(
                        id={"type": self.operation_id, "index": index},
                        style={"minWidth": "100%"},
                        multi=False,
                        clearable=True,
                        placeholder="----",
                        value=None,
                    ),
                ),
                dbc.Col(
                    id={"type": self.filter_val_obj_id, "index": index},
                    children=dcc.Input(
                        id={"type": self.filter_val_id, "index": index},
                        style={"minWidth": "100%", "display": "block"},
                        placeholder="----",
                        value=None,
                        type="text",
                    ),
                ),
                dbc.Col(
                    dbc.Button(
                        className=f"fas fa-x", id={"type": self.remove_filter_btn_id, "index": index}, color="secondary"
                    ),
                    width=1,
                ),
            ],
            style={"margin": "10px"},
        )
        return single_filter_initial_layout

    @staticmethod
    def get_empty_index(base_ind: int, filters_list, max_filters_per_group: int):
        existing_indexes = list(single_filter["props"]["id"]["index"] for single_filter in filters_list)
        for ind in range(base_ind, base_ind + max_filters_per_group):
            if ind not in existing_indexes:
                return ind
        return None

    @staticmethod
    def get_distinct_string_values(column: Column, main_tables: list[Base], md_tables: list[Base]):
        base_query = base_data_subquery(
            main_tables=main_tables,
            terms=[column],
            meta_data_tables=md_tables,
        )
        distinct_query = Query.from_(base_query).select(column.alias).distinct().limit(30)
        distinct_values = execute(distinct_query)[column.alias]
        return distinct_values

    @staticmethod
    def get_united_columns_dict(main_data: str, md_table: str = None) -> list[str]:
        columns = EXISTING_TABLES[main_data].get_columns()
        if md_table:
            md_columns = EXISTING_TABLES[md_table].get_columns()
            columns = list(set(columns + md_columns))

        return columns

    @staticmethod
    def get_column_from_tables(column_name: str, main_data: str, md_table: str = None) -> Column:
        column = getattr(EXISTING_TABLES[main_data], column_name, None)
        if (not column) and md_table:
            column = getattr(EXISTING_TABLES[md_table], column_name, None)

        return column

    def recursive_build_meta_data_filters(self, filters) -> Criterion:
        # removed filter case
        if filters["props"]["style"].get("display") == "none":
            return EmptyCriterion()

        # single filter case
        if filters["props"]["id"]["type"] == self.filter_id:
            row = filters["props"]
            column: str = row["children"][0]["props"]["children"]["props"]["value"]
            operation: str = row["children"][1]["props"]["children"]["props"]["value"]
            if not column or not operation:
                return EmptyCriterion()

            column: Column = self.get_column_from_tables(column, self.main_table, META_DATA)
            operation: Callable = getattr(column, operation)
            value: str = row["children"][2]["props"]["children"]["props"]["value"]
            single_filter = operation(column.type(value)) if value is not None else operation()
            return single_filter

        # group case
        or_and = (
            Criterion.any if filters["props"]["children"][0]["props"]["children"][0]["props"]["on"] else Criterion.all
        )
        filters = filters["props"]["children"][1]["props"]["children"]
        sub_filters = [self.recursive_build_meta_data_filters(flt) for flt in filters]
        return or_and(sub_filters)
