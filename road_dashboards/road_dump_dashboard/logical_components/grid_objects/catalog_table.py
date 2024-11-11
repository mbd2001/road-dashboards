import base64
import json

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dash_table, html, no_update
from road_database_toolkit.dynamo_db.db_manager import DBManager

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import URL
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import card_wrapper
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject

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
        self.column_selector_id = self._generate_id("column_selector")
        self.update_runs_btn_id = self._generate_id("update_runs_btn")

    def layout(self):
        catalog_layout = card_wrapper(
            [
                dbc.Row(html.H2("Datasets Catalog", className="mb-5")),
                dbc.Row(dbc.Col(self.get_column_selector(self.column_selector_id), width={"size": 12})),
                dbc.Row(self.get_data_table(self.dump_catalog_id)),
                dbc.Row(
                    dbc.Col(
                        dbc.Button(
                            "Choose Datasets to Explore", id=self.update_runs_btn_id, className="bg-primary mt-5"
                        )
                    ),
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
                    className="dropdown-item",
                    inputClassName="me-2",
                )
            ],
            right=True,
            color="secondary",
            style={"position": "absolute", "right": "10px", "top": "10px"},
        )

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
            style_cell={"textAlign": "left"},
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
        @callback(Output(self.dump_catalog_id, "data"), Input(self.dump_catalog_id, "id"))
        def update_catalog_data(dummy_trigger):
            catalog_data = pd.DataFrame(dump_db_manager.scan(), columns=list(table_columns.keys()))
            catalog_data["total_frames"] = catalog_data["total_frames"].apply(lambda x: sum(x.values()))
            catalog_data_dict = catalog_data.to_dict("records")
            return catalog_data_dict

        @callback(Output(self.dump_catalog_id, "columns"), Input(self.column_selector_id, "value"))
        def update_catalog_columns(selected_columns):
            return [{"name": name, "id": col} for col, name in table_columns.items() if col in selected_columns]

        @callback(
            Output(URL, "hash"),
            Input(self.update_runs_btn_id, "n_clicks"),
            State(self.dump_catalog_id, "derived_virtual_data"),
            State(self.dump_catalog_id, "derived_virtual_selected_rows"),
        )
        def init_run(n_clicks, rows, derived_virtual_selected_rows):
            if not derived_virtual_selected_rows:
                return no_update

            datasets_ids = self.parse_catalog_rows(rows, derived_virtual_selected_rows)["dump_name"]
            datasets = [dump_db_manager.get_item(dataset_id) for dataset_id in datasets_ids]
            datasets = pd.DataFrame(datasets)

            dumps_list = list(datasets["dump_name"])
            dump_list_hash = "#" + base64.b64encode(json.dumps(dumps_list).encode("utf-8")).decode("utf-8")
            return dump_list_hash

    @staticmethod
    def parse_catalog_rows(rows, derived_virtual_selected_rows):
        rows = pd.DataFrame([rows[i] for i in derived_virtual_selected_rows])
        return rows
