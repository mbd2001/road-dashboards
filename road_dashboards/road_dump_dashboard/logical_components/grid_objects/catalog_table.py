import base64
import json

import dash_bootstrap_components as dbc
import dash_daq as daq
import pandas as pd
from angie_shuffle_service.shuffle_service import (
    get_dataset,
)
from boto3.dynamodb.conditions import Attr
from dash import Input, Output, State, callback, dash_table, html, no_update
from road_database_toolkit.dynamo_db.db_manager import DBManager

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import MEXSENSE_DATA, URL
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.logical_components.mexsense_link import get_mexsense_link

dump_db_manager = DBManager(table_name="algoroad_dump_catalog", primary_key="dump_name")

table_columns = {
    "dump_name": "Dataset Name",
    "use_case": "Use Case",
    "user": "User",
    "total_frames": "Total Frames",
    "last_change": "Last Change",
    "brain": "Brain",
    "jira": "JIRA",
}
default_unchecked_columns = ["brain", "jira"]


class CatalogTable(GridObject):
    def __init__(
        self,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.dump_catalog_id = self._generate_id("dump_catalog")
        self.filter_not_completed_switch_id = self._generate_id("filter_not_completed_switch")
        self.column_selector_id = self._generate_id("column_selector")
        self.update_runs_btn_id = self._generate_id("update_runs_btn")
        self.mexsense_btn = self._generate_id("mexsense_btn")

    def layout(self):
        column_selector = self.get_column_selector(self.column_selector_id)
        filter_not_completed_switch = self.get_filter_not_completed_switch(self.filter_not_completed_switch_id)
        data_table = self.get_data_table(self.dump_catalog_id)
        catalog_layout = card_wrapper(
            [
                dbc.Row(
                    [dbc.Col(html.H2("Datasets Catalog")), dbc.Col([filter_not_completed_switch, column_selector])]
                ),
                dbc.Row(loading_wrapper(data_table), className="mt-5"),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                "Choose Datasets to Explore",
                                id=self.update_runs_btn_id,
                                className="bg-primary mt-5",
                            ),
                            width="auto",
                            className="me-1",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Open in MExsense",
                                id=self.mexsense_btn,
                                className="btn btn-primary mt-5",
                                href="",
                                target="_blank",
                                style={"display": "inline-block"},
                            ),
                            width="auto",
                            className="ms-1",
                        ),
                    ],
                    justify="start",
                ),
            ]
        )
        return catalog_layout

    @staticmethod
    def get_column_selector(obj_id: str):
        return dbc.DropdownMenu(
            label="Select Columns",
            children=[
                dbc.Checklist(
                    options=table_columns,
                    value=[col for col in table_columns.keys() if col not in default_unchecked_columns],
                    id=obj_id,
                    inline=False,
                    className="me-2",
                )
            ],
            align_end=True,
            color="secondary",
            style={"position": "absolute", "right": "10px", "top": "10px"},
        )

    @staticmethod
    def get_filter_not_completed_switch(filter_not_completed_switch_id: str):
        filter_not_completed_switch = daq.BooleanSwitch(
            id=filter_not_completed_switch_id,
            on=True,
            label="Show All <-> Filter not completed",
            labelPosition="top",
            style={"position": "absolute", "right": "200px", "top": "10px"},
        )
        return filter_not_completed_switch

    @staticmethod
    def get_data_table(obj_id: str):
        return dash_table.DataTable(
            id=obj_id,
            columns=[],
            data=[],
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            sort_by=[{"column_id": "last_change", "direction": "desc"}],
            row_selectable="multi",
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=20,
            css=[{"selector": ".show-hide", "rule": "display: none"}],
            style_cell={"textAlign": "left", "paddingLeft": "10px"},
            style_cell_conditional=[
                {"if": {"column_id": "total_frames"}, "textAlign": "right", "paddingRight": "10px", "width": "10%"},
                {
                    "if": {"column_id": "last_change"},
                    "textAlign": "center",
                },
            ],
            style_header={
                "background-color": "#4e4e50",
                "fontWeight": "bold",
                "color": "white",
            },
            style_data={
                "backgroundColor": "white",
                "color": "rgb(102, 102, 102)",
            },
            style_table={
                "border": "1px solid rgb(230, 230, 230)",
            },
        )

    def _callbacks(self):
        @callback(
            Output(self.dump_catalog_id, "data"),
            Input(self.dump_catalog_id, "id"),
            Input(self.filter_not_completed_switch_id, "on"),
        )
        def update_catalog_data(dummy_trigger, filter_not_completed):
            filter_condition = {"FilterExpression": Attr("stage").eq("done")} if filter_not_completed else {}
            catalog_data = pd.DataFrame(dump_db_manager.scan(**filter_condition), columns=list(table_columns.keys()))
            catalog_data["total_frames"] = catalog_data["total_frames"].apply(lambda x: sum(x.values()))
            catalog_data_dict = catalog_data.to_dict("records")
            return catalog_data_dict

        @callback(Output(self.dump_catalog_id, "columns"), Input(self.column_selector_id, "value"))
        def update_catalog_columns(selected_columns):
            long_number_format = {"type": "numeric", "format": {"specifier": ".3s"}}
            columns_config = [
                {"name": name, "id": col} for col, name in table_columns.items() if col in selected_columns
            ]
            for col_conf in columns_config:
                if col_conf["name"] == "Total Frames":
                    col_conf.update(long_number_format)

            return columns_config

        @callback(
            [Output(URL, "hash"), Output(MEXSENSE_DATA, "data")],
            Input(self.update_runs_btn_id, "n_clicks"),
            State(self.dump_catalog_id, "derived_virtual_data"),
            State(self.dump_catalog_id, "derived_virtual_selected_rows"),
            prevent_initial_call=True,
        )
        def init_run(n_clicks, rows, derived_virtual_selected_rows):
            if not derived_virtual_selected_rows:
                return no_update, ""

            datasets_ids = self.parse_catalog_rows(rows, derived_virtual_selected_rows)["dump_name"]
            datasets = [dump_db_manager.get_item(dataset_id) for dataset_id in datasets_ids]
            datasets = pd.DataFrame(datasets)

            dumps_list = list(datasets["dump_name"])
            dump_list_hash = "#" + base64.b64encode(json.dumps(dumps_list).encode("utf-8")).decode("utf-8")
            shuffle_path = self.get_shuffle_path(rows, derived_virtual_selected_rows)
            return dump_list_hash, shuffle_path

        @callback(
            Output(self.mexsense_btn, "href"),
            [Input(self.mexsense_btn, "n_clicks")],
            [Input(self.dump_catalog_id, "derived_virtual_selected_rows")],
            [State(self.dump_catalog_id, "derived_virtual_data")],
            prevent_initial_call=True,
        )
        def mexsense_run(n_clicks, selected_rows, rows):
            return "about:blank"

            if not selected_rows:
                return "about:blank"

            shuffle_path = self.get_shuffle_path(rows, selected_rows)
            link = get_mexsense_link(shuffle_path)
            return link

    @staticmethod
    def parse_catalog_rows(rows, derived_virtual_selected_rows):
        rows = pd.DataFrame([rows[i] for i in derived_virtual_selected_rows])
        return rows

    @staticmethod
    def get_shuffle_path(rows, selected_rows):
        rows = pd.DataFrame([rows[i] for i in selected_rows])

        dataset_name = rows["dump_name"].iloc[0]
        use_case = rows["use_case"].iloc[0]
        shuffle_path = get_dataset(use_case=use_case, name=dataset_name)
        return shuffle_path.path
