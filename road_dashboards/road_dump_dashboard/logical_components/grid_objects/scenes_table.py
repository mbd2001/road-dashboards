from dataclasses import dataclass

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, callback, dash_table, html, no_update
from pypika import Case, Criterion, EmptyCriterion, functions
from pypika.terms import Term

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import base_data_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import execute, load_object, optional_inputs
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


@dataclass
class Scene:
    definition: Criterion
    name: str
    required_frames: int

    def count(self) -> Term:
        return functions.Sum(Case().when(self.definition, 1).else_(0)).as_(self.name)


SCENES: list[Scene] = [
    Scene(MetaData.hwe == False, "HWE", 100),
    Scene(MetaData.hwe == True, "TEST", 100),
]


class ScenesTable(GridObject):
    def __init__(
        self,
        datasets_dropdown_id: str,
        page_filters_id: str = "",
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.datasets_dropdown_id = datasets_dropdown_id
        self.page_filters_id = page_filters_id
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.scenes_table_id = self._generate_id("scenes_table")
        self.only_failed_id = self._generate_id("only_failed")

    def layout(self):
        shown_columns = ["scene", "num_of_frames", "required_frames", "percentage"]
        scenes_table = dash_table.DataTable(
            id=self.scenes_table_id,
            columns=[{"name": i, "id": i, "deletable": False, "selectable": True} for i in shown_columns],
            data=[],
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            sort_by=[{"column_id": "percentage", "direction": "desc"}],
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
            style_data_conditional=[
                {
                    "if": {
                        "filter_query": "{percentage} < 90",
                    },
                    "backgroundColor": "OrangeRed",
                    "color": "white",
                },
                {
                    "if": {
                        "filter_query": "{percentage} >= 100",
                    },
                    "backgroundColor": "ForestGreen",
                    "color": "white",
                },
            ],
        )
        only_failed_switch = daq.BooleanSwitch(
            id=self.only_failed_id, on=False, label="Insufficient Scenes", labelPosition="top", className="me-2"
        )
        return card_wrapper(
            [
                dbc.Row([dbc.Col(html.H2("Scenes Distribution", className="mb-5")), dbc.Col(only_failed_switch)]),
                dbc.Row(loading_wrapper(scenes_table)),
            ]
        )

    def _callbacks(self):
        @callback(
            Output(self.scenes_table_id, "data"),
            Output(self.scenes_table_id, "tooltip_data"),
            Input(self.datasets_dropdown_id, "value"),
            Input(META_DATA, "data"),
            Input(self.only_failed_id, "on"),
            optional_inputs(page_filters=Input(self.page_filters_id, "data")),
        )
        def update_scenes_data(chosen_dump, md_tables, only_failed, optional):
            if not md_tables or not chosen_dump:
                return no_update, no_update

            md_tables: list[Base] = load_object(md_tables)
            page_filters: str = optional.get("page_filters", None)
            page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()

            tables = [table for table in md_tables if table.dataset_name == chosen_dump]
            base = base_data_subquery(
                main_tables=tables,
                meta_data_tables=tables,
                terms=[scene.count() for scene in SCENES],
                page_filters=page_filters,
                to_order=False,
            )
            results = execute(base)
            table_data = [
                {
                    "scene": scene.name,
                    "num_of_frames": results[scene.name][0],
                    "required_frames": scene.required_frames,
                    "percentage": results[scene.name][0] / scene.required_frames * 100.0,
                }
                for scene in SCENES
            ]
            if only_failed:
                table_data = [scene for scene in table_data if scene["percentage"] < 90]

            tooltip_data = [{"scene": {"value": str(scene.definition), "type": "markdown"}} for scene in SCENES]
            return table_data, tooltip_data
