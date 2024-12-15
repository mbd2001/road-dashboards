import base64
import json

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dash_table, dcc, html, no_update
from pypika import Criterion, EmptyCriterion, Query, functions

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import base_data_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.catalog_table import dump_db_manager
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import execute, load_object, optional_inputs
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class BoostingControl(GridObject):
    def __init__(
        self,
        datasets_dropdown_id: str,
        population_dropdown_id: str,
        page_filters_id: str = "",
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.datasets_dropdown_id = datasets_dropdown_id
        self.population_dropdown_id = population_dropdown_id
        self.page_filters_id = page_filters_id
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.batches_table_id = self._generate_id("status_table")
        self.upload_boosting_btn_id = self._generate_id("load_boosting_btn")
        self.download_boosting_btn_id = self._generate_id("download_boosting_btn")
        self.upload_data_id = self._generate_id("upload_data")
        self.download_data_id = self._generate_id("download_data")

    def layout(self):
        header = self.get_header_layout(self.upload_boosting_btn_id, self.download_boosting_btn_id)
        batches_table = self.get_table_layout(self.batches_table_id)
        upload_data = dcc.Store(id=self.upload_data_id)
        download_data = loading_wrapper(dcc.Download(id=self.download_data_id))
        final_layout = card_wrapper([header, upload_data, download_data, batches_table])
        return final_layout

    def _callbacks(self):
        @callback(
            Output(self.batches_table_id, "data", allow_duplicate=True),
            Output(self.batches_table_id, "tooltip_data"),
            Input(META_DATA, "data"),
            Input(self.datasets_dropdown_id, "value"),
            Input(self.population_dropdown_id, "value"),
            State(self.upload_data_id, "data"),
            optional_inputs(page_filters=Input(self.page_filters_id, "data")),
            prevent_initial_call=True,
        )
        def update_batches_table(tables, chosen_dump, population, json_data, optional):
            if not tables or not chosen_dump or not population:
                return no_update, no_update

            page_filters: str = optional.get("page_filters", None)
            page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()
            tables: list[Base] = load_object(tables)

            conditions_list = self.get_conditions_list(chosen_dump, population)
            batches_df = self.get_batches_count(chosen_dump, tables, page_filters)
            batches_df["batch_name"] = batches_df["batch_num"].apply(
                lambda batch_num: next(iter(conditions_list[batch_num]))
            )
            if json_data:
                weights_dict = json_data["data"][population]["batch_sampling_rate"]
                batches_df["weight"] = batches_df["batch_name"].apply(lambda x: weights_dict.get(x, 0))
            else:
                batches_df["weight"] = [1] * len(batches_df.index)

            batches_df["normalized_weight"] = (batches_df["weight"] / batches_df["weight"].sum()).round(3)
            tooltip_data = [
                {"batch_name": {"value": next(iter(conditions_list[batch_num].values())), "type": "markdown"}}
                for batch_num in batches_df["batch_num"]
            ]
            return batches_df.to_dict("records"), tooltip_data

        @callback(
            Output(self.batches_table_id, "data", allow_duplicate=True),
            Input(self.upload_data_id, "data"),
            State(self.population_dropdown_id, "value"),
            State(self.batches_table_id, "data"),
            prevent_initial_call=True,
        )
        def update_batches_table_from_json(json_data, population, table_data):
            if not json_data:
                return no_update

            weights_dict = json_data["data"][population]["batch_sampling_rate"]
            for row in table_data:
                row["weight"] = weights_dict.get(row["batch_name"], 0)

            return table_data

        @callback(
            Output(self.batches_table_id, "data"),
            Input(self.batches_table_id, "data_timestamp"),
            State(self.batches_table_id, "data"),
        )
        def update_batches_table_from_user_input(timestamp, table_data):
            if not table_data:
                return no_update

            weights_sum = sum(row["weight"] for row in table_data)
            for row in table_data:
                row["normalized_weight"] = round(row["weight"] / weights_sum, 3)

            return table_data

        @callback(
            Output(self.upload_data_id, "data"),
            Input(self.upload_boosting_btn_id, "contents"),
        )
        def upload_existing_boosting(data):
            if not data:
                return no_update

            content_type, content_string = data.split(",")
            json_file = json.loads(base64.b64decode(content_string).decode("utf8"))
            return json_file

        @callback(
            Output(self.download_data_id, "data"),
            Input(self.download_boosting_btn_id, "n_clicks"),
            State(self.upload_data_id, "data"),
            State(self.batches_table_id, "data"),
            State(self.population_dropdown_id, "value"),
        )
        def download_boosting(n_clicks, json_file, bathes_table, population):
            if not json_file or not bathes_table:
                return no_update

            updated_batch_to_weight = {row["batch_name"]: row["weight"] for row in bathes_table}
            json_file["data"][population]["batch_sampling_rate"] = {
                batch_name: updated_batch_to_weight.get(batch_name, 0)
                for batch_name, _ in json_file["data"][population]["batch_sampling_rate"].items()
            }
            jump_name = "tmp_name"
            return dict(content=json_file, filename=f"{jump_name}.jump")

    @staticmethod
    def get_conditions_list(chosen_dump: str, population: str) -> list[dict[str, str]]:
        conditions_dict = dump_db_manager.get_item(chosen_dump).get("split_conditions", {})
        conditions = conditions_dict.get(f"{population}_batch_conditions", {})
        return [{"unfiltered": ""}] + conditions

    @staticmethod
    def get_batches_count(chosen_dump: str, tables: list[Base], page_filters: Criterion) -> pd.DataFrame:
        tables = [table for table in tables if table.dataset_name == chosen_dump]
        batch_num = MetaData.batch_num
        base = base_data_subquery(
            main_tables=tables,
            meta_data_tables=tables,
            terms=[batch_num],
            page_filters=page_filters,
        )
        query = (
            Query.from_(base)
            .groupby(batch_num.alias)
            .select(batch_num.alias, functions.Count("*", "num_frames"))
            .orderby(batch_num)
        )
        data = execute(query)
        return data

    @staticmethod
    def get_header_layout(load_boosting_btn_id, download_boosting_btn_id):
        load_boosting_btn = dcc.Upload(
            children=html.Div("Drag and Drop or Select Json"),
            id=load_boosting_btn_id,
            accept="application/json",
            style={
                "width": "100%",
                "height": "40px",
                "lineHeight": "40px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
        )
        download_boosting_btn = dbc.Button("Download New Boosting", id=download_boosting_btn_id, color="primary")
        header = dbc.Row(
            [
                dbc.Col(html.H2("Boosting Control")),
                dbc.Col(
                    dbc.Stack(
                        [load_boosting_btn, download_boosting_btn],
                        direction="horizontal",
                        gap=4,
                        style={"position": "absolute", "right": "10px", "top": "10px"},
                        className="me-2",
                    )
                ),
            ]
        )
        return header

    @staticmethod
    def get_table_layout(batches_table_id):
        shown_columns = ["batch_num", "batch_name", "num_frames", "weight", "normalized_weight"]
        batches_table = dash_table.DataTable(
            id=batches_table_id,
            columns=[
                {
                    "name": i,
                    "id": i,
                    "deletable": False,
                    "editable": i == "weight",
                    "type": "text" if i == "batch_name" else "numeric",
                }
                for i in shown_columns
            ],
            data=[],
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            sort_by=[{"column_id": "batch_num", "direction": "asc"}],
            page_action="native",
            page_current=0,
            page_size=256,
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
                "lineHeight": "33px",
            },
            style_table={
                "border": "1px solid rgb(230, 230, 230)",
            },
        )
        batches_table = html.Div(batches_table, className="mt-5")
        return batches_table
