import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Input, Output, State, callback, dash_table, dcc, html, no_update
from pypika import Case, Criterion, EmptyCriterion, Query, functions

from road_dashboards.road_dump_dashboard.graphical_components.pie_chart import basic_pie_chart
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import base_data_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.catalog_table import dump_db_manager
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.scenes_table import SCENES
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import execute, load_object, optional_inputs
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class BatchesTable(GridObject):
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
        self.sliders_div_id = self._generate_id("sliders_div")
        self.slider_id = self._generate_id("slider")
        self.scenes_pie_id = self._generate_id("state_pie")

    def layout(self):
        shown_columns = ["batch_num", "batch_name", "num_frames"]
        batches_table = dash_table.DataTable(
            id=self.batches_table_id,
            columns=[{"name": i, "id": i, "deletable": False, "selectable": True} for i in shown_columns],
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
        batches_graph = dcc.Graph(
            id=self.scenes_pie_id,
            config={"displayModeBar": False},
        )
        final_layout = card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(loading_wrapper(batches_table)),
                        dbc.Col(loading_wrapper(html.Div(id=self.sliders_div_id, style={"margin-top": "75px"}))),
                    ]
                ),
                dbc.Row(loading_wrapper(batches_graph)),
            ]
        )
        return final_layout

    def _callbacks(self):
        @callback(
            Output(self.batches_table_id, "data"),
            Output(self.sliders_div_id, "children"),
            Input(META_DATA, "data"),
            Input(self.datasets_dropdown_id, "value"),
            Input(self.population_dropdown_id, "value"),
            optional_inputs(page_filters=Input(self.page_filters_id, "data")),
        )
        def update_batches_table(tables, chosen_dump, population, optional):
            if not tables or not chosen_dump or not population:
                return no_update, no_update

            page_filters: str = optional.get("page_filters", None)
            page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()
            tables: list[Base] = load_object(tables)

            conditions_list = self.get_conditions_list(chosen_dump, population)
            batches_df = self.get_batches_count(chosen_dump, tables, page_filters)
            batches_df["batch_name"] = batches_df["batch_num"].apply(lambda x: conditions_list[x])

            default_value = 1 / len(batches_df.index)
            sliders = [
                dcc.Slider(
                    0,
                    1,
                    id={"type": self.slider_id, "index": batch_num},
                    marks=None,
                    value=default_value,
                )
                for batch_num in batches_df["batch_num"]
            ]
            # tooltip_data=[{"batch_name": {"value": str(conditions_list[batch_name]), "type": "markdown"}} for batch_name in batches_df["batch_name"]]
            return batches_df.to_dict("records"), sliders

        @callback(
            Output(self.scenes_pie_id, "figure"),
            Input({"type": self.slider_id, "index": ALL}, "value"),
            State({"type": self.slider_id, "index": ALL}, "id"),
            State(META_DATA, "data"),
            State(self.datasets_dropdown_id, "value"),
            State(self.population_dropdown_id, "value"),
            optional_inputs(page_filters=State(self.page_filters_id, "data")),
        )
        def update_batches_table(slider_values, slider_indices, tables, chosen_dump, population, optional):
            if not tables or not chosen_dump or not population:
                return no_update

            slider_indices = [idx["index"] for idx in slider_indices]
            batch_num = MetaData.batch_num
            batches_weight_case = Case(alias="batch_weight")
            for val, idx in zip(slider_values, slider_indices):
                batches_weight_case = batches_weight_case.when(batch_num == idx, val)

            page_filters: str = optional.get("page_filters", None)
            page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()
            tables: list[Base] = load_object(tables)

            data = self.weighted_scenes_query(chosen_dump, tables, page_filters, batches_weight_case)
            data = pd.melt(data, var_name="scene", value_name="weight")
            data["definition"] = [str(scene.definition) for scene in SCENES]
            fig = basic_pie_chart(data, "scene", "weight", title="Scenes Distribution", hover="definition")
            return fig

    @staticmethod
    def get_conditions_list(chosen_dump: str, population: str) -> list[str]:
        conditions_dict = dump_db_manager.get_item(chosen_dump).get("split_conditions", {})
        conditions = conditions_dict.get(f"{population}_batch_conditions", {})
        return ["unfiltered"] + [next(iter(cond)) for cond in conditions]

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
    def weighted_scenes_query(chosen_dump: str, tables: list[Base], page_filters: Criterion, batches_weight_case: Case) -> pd.DataFrame:
        tables=[table for table in tables if table.dataset_name == chosen_dump]
        base_terms = [col for scene in SCENES for col in scene.definition.find_(Column)]

        base = base_data_subquery(
            main_tables=tables,
            meta_data_tables=tables,
            terms=list({*base_terms, batches_weight_case}),
            page_filters=page_filters,
        )
        scenes_query = Query.from_(base).select(
            *[
                functions.Sum(Case().when(scene.definition, base.batch_weight).else_(0)).as_(scene.name)
                for scene in SCENES
            ]
        )
        data = execute(scenes_query)
        return data
