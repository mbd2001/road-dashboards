import base64
import json

import dash_bootstrap_components as dbc
import pandas as pd
import yaml
from dash import Input, Output, State, callback, dash_table, dcc, html, no_update
from pypika import Case, Criterion, EmptyCriterion, Query, functions
from pypika.terms import LiteralValue

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import loading_wrapper
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import base_data_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.catalog_table import dump_db_manager
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import execute, load_object, optional_inputs


class BoostingControl(GridObject):
    """
    Grid object that contains 4 main components:
        1. Table with batches and their weights (default 1)
        2. Upload button for splitting yaml file
        3. Upload button for boosting json file
        4. Download button for updated boosting json file

    The table is updated based on the chosen dataset and population, and can be edited by the user.
    The user can upload a json file with existing boosting weights, and download a json file with updated weights.
    """

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
        self.batches_table_id = self._generate_id("batches_table")
        self.upload_boosting_btn_id = self._generate_id("upload_boosting_btn")
        self.uploaded_boosting_id = self._generate_id("uploaded_boosting")

        self.download_boosting_btn_id = self._generate_id("download_boosting_btn")
        self.download_boosting_id = self._generate_id("download_boosting")

        self.upload_split_btn_id = self._generate_id("upload_split_btn")
        self.uploaded_split_id = self._generate_id("uploaded_split")

    def layout(self):
        header = self.get_header_layout(
            self.upload_split_btn_id,
            self.upload_boosting_btn_id,
            self.download_boosting_btn_id,
            self.download_boosting_id,
        )
        batches_table = self.get_table_layout(self.batches_table_id)
        uploaded_boosting = dcc.Store(id=self.uploaded_boosting_id)
        uploaded_split = dcc.Store(id=self.uploaded_split_id)
        final_layout = html.Div([header, batches_table, uploaded_boosting, uploaded_split])
        return final_layout

    def _callbacks(self):
        @callback(
            Output(self.batches_table_id, "data", allow_duplicate=True),
            Output(self.batches_table_id, "tooltip_data"),
            Input(META_DATA, "data"),
            Input(self.datasets_dropdown_id, "value"),
            Input(self.population_dropdown_id, "value"),
            Input(self.uploaded_boosting_id, "data"),
            Input(self.uploaded_split_id, "data"),
            optional_inputs(page_filters=Input(self.page_filters_id, "data")),
            prevent_initial_call=True,
        )
        def update_batches_table(
            tables: str,
            chosen_dataset: str,
            population: str,
            boosting_data: dict | None,
            split_data: dict | None,
            optional: dict,
        ):
            """Update table from page inputs"""
            if not tables or not chosen_dataset or not population:
                return no_update, no_update

            page_filters: str = optional.get("page_filters", None)
            page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()
            tables: list[Base] = load_object(tables)

            conditions_list = self.get_conditions_list(chosen_dataset, population, split_data)
            batches_df = self.get_batches_count(chosen_dataset, tables, page_filters, conditions_list)
            batches_df["weight"] = self.get_batches_weight(batches_df, population, boosting_data)

            table_data = batches_df.to_dict("records")
            self.update_normalized_weight(table_data)
            tooltip_data = [
                {"batch_name": {"value": next(iter(conditions_list[row["batch_num"]].values())), "type": "markdown"}}
                for row in table_data
            ]
            return table_data, tooltip_data

        @callback(
            Output(self.batches_table_id, "data", allow_duplicate=True),
            Input(self.uploaded_boosting_id, "data"),
            State(self.population_dropdown_id, "value"),
            State(self.batches_table_id, "data"),
            prevent_initial_call=True,
        )
        def update_batches_table_from_json(boosting_data: dict, population: str, table_data: list[dict]):
            """Update table with weights from uploaded json"""
            if not boosting_data:
                return no_update

            weights_dict = boosting_data["data"][population]["batch_sampling_rate"]
            for row in table_data:
                row["weight"] = weights_dict.get(row["batch_name"], 0)

            self.update_normalized_weight(table_data)
            return table_data

        @callback(
            Output(self.batches_table_id, "data"),
            Input(self.batches_table_id, "data_timestamp"),
            State(self.batches_table_id, "data"),
        )
        def update_batches_table_from_user_input(timestamp: int, table_data: list[dict]):
            """Update normalized weights after user input"""
            if not table_data:
                return no_update

            self.update_normalized_weight(table_data)
            return table_data

        @callback(
            Output(self.uploaded_boosting_id, "data"),
            Input(self.upload_boosting_btn_id, "contents"),
        )
        def upload_existing_boosting(data: str):
            """Upload json file with existing weights"""
            if not data:
                return no_update

            content_type, content_string = data.split(",")
            json_file = json.loads(base64.b64decode(content_string).decode("utf8"))
            return json_file

        @callback(
            Output(self.uploaded_split_id, "data"),
            Input(self.upload_split_btn_id, "contents"),
        )
        def upload_existing_split(data: str):
            """Upload yaml file with existing split conditions"""
            if not data:
                return no_update

            content_type, content_string = data.split(",")
            encoded_data = base64.b64decode(content_string).decode("utf8")
            split_conditions = yaml.safe_load(encoded_data)
            ordered_conditions = {}
            for population, conditions in split_conditions.items():
                ordered_conditions[population] = [{name: cond} for name, cond in conditions.items()]

            return ordered_conditions

        @callback(
            Output(self.download_boosting_id, "data"),
            Input(self.download_boosting_btn_id, "n_clicks"),
            State(self.uploaded_boosting_id, "data"),
            State(self.batches_table_id, "data"),
            State(self.population_dropdown_id, "value"),
        )
        def download_boosting(n_clicks: int, json_file: dict, batches_table: dict, population: str):
            """Download json file with updated weights"""
            if not json_file or not batches_table:
                return no_update

            updated_batch_to_weight = {row["batch_name"]: row["weight"] for row in batches_table}
            json_file["data"][population]["batch_sampling_rate"] = {
                batch_name: updated_batch_to_weight.get(batch_name, 0)
                for batch_name, _ in json_file["data"][population]["batch_sampling_rate"].items()
            }
            jump_name = "tmp_name"
            return dict(content=json.dumps(json_file, indent=4), filename=f"{jump_name}.json")

    @staticmethod
    def update_normalized_weight(table_data: list[dict]):
        weights_sum = sum(row["weight"] for row in table_data)
        for row in table_data:
            row["normalized_weight"] = round(row["weight"] / weights_sum, 3)

    @staticmethod
    def get_conditions_list(
        chosen_dataset: str, population: str, split_data: dict[str, list[dict[str, str]]] | None
    ) -> list[dict[str, str]]:
        conditions_dict = split_data or dump_db_manager.get_item(chosen_dataset).get("split_conditions", {})
        conditions = conditions_dict.get(f"{population}_batch_conditions") or conditions_dict["all_batch_conditions"]
        return [{"unfiltered": "TRUE"}] + conditions

    @staticmethod
    def get_batches_count(
        chosen_dataset: str, tables: list[Base], page_filters: Criterion, conditions_list: list[dict[str, str]]
    ) -> pd.DataFrame:
        tables = [table for table in tables if table.dataset_name == chosen_dataset]
        assert len(tables) == 1, f"Expected one table for dataset {chosen_dataset}, got {len(tables)}"
        batch_num_col = Case(alias="batch_num")
        for batch_num in range(len(conditions_list) - 1, -1, -1):
            condition = next(iter(conditions_list[batch_num].values()))
            batch_num_col = batch_num_col.when(LiteralValue(condition), batch_num)

        base = base_data_subquery(
            main_tables=tables,
            meta_data_tables=tables,
            terms=[batch_num_col],
            page_filters=page_filters,
            to_order=False,
        )
        query = (
            Query.from_(base)
            .groupby(batch_num_col.alias)
            .select(batch_num_col.alias, functions.Count("*", "num_frames"))
            .orderby(batch_num_col.alias)
        )
        data = execute(query)
        data["batch_name"] = data["batch_num"].apply(lambda batch_num: next(iter(conditions_list[batch_num])))
        return data

    @staticmethod
    def get_batches_weight(batches_df: pd.DataFrame, population: str, boosting_data: dict | None) -> list[float]:
        if not boosting_data:
            return [1] * len(batches_df.index)

        weights_dict = boosting_data["data"][population]["batch_sampling_rate"]
        return batches_df["batch_name"].apply(lambda x: weights_dict.get(x, 0))

    @staticmethod
    def get_header_layout(
        upload_split_btn_id: str, upload_boosting_btn_id: str, download_boosting_btn_id: str, download_boosting_id: str
    ):
        upload_split_btn = dcc.Upload(
            children=html.Div("Drag and Drop or Select Split file"),
            id=upload_split_btn_id,
            accept=".yaml, .yml",
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

        upload_boosting_btn = dcc.Upload(
            children=html.Div("Drag and Drop or Select Boosting file"),
            id=upload_boosting_btn_id,
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
        download_boosting = loading_wrapper(dcc.Download(id=download_boosting_id))

        header = dbc.Stack(
            [upload_split_btn, upload_boosting_btn, download_boosting_btn, download_boosting],
            direction="horizontal",
            gap=4,
            className="mt-3",
        )
        return header

    @staticmethod
    def get_table_layout(batches_table_id: str):
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
        return html.Div(batches_table, className="mt-3")
