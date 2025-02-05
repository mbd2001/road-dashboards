import pandas as pd
from dash import Input, Output, State, callback, dcc, no_update
from pypika import Case, Criterion, EmptyCriterion, Query
from pypika.terms import LiteralValue

from road_dashboards.road_dump_dashboard.graphical_components.pie_chart import basic_pie_chart
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import base_data_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import execute, load_object, optional_inputs
from road_dashboards.road_dump_dashboard.table_schemes.scenes import ScenesCategory


class ScenesPie(GridObject):
    def __init__(
        self,
        datasets_dropdown_id: str,
        population_dropdown_id: str,
        batches_table_id: str,
        scene_category: ScenesCategory,
        page_filters_id: str = "",
        title: str = "",
        full_grid_row: bool = False,
        component_id: str = "",
    ):
        self.datasets_dropdown_id = datasets_dropdown_id
        self.population_dropdown_id = population_dropdown_id
        self.batches_table_id = batches_table_id
        self.scene_category = scene_category
        self.page_filters_id = page_filters_id
        self.title = title if title else f"{scene_category.name} Distribution"
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.scenes_pie_id = self._generate_id("state_pie")

    def layout(self):
        batches_graph = dcc.Graph(
            id=self.scenes_pie_id,
            config={"displayModeBar": False},
        )
        return card_wrapper(loading_wrapper(batches_graph))

    def _callbacks(self):
        @callback(
            Output(self.scenes_pie_id, "figure"),
            Input(self.batches_table_id, "data"),
            Input(self.batches_table_id, "tooltip_data"),
            State(META_DATA, "data"),
            State(self.datasets_dropdown_id, "value"),
            State(self.population_dropdown_id, "value"),
            optional_inputs(page_filters=State(self.page_filters_id, "data")),
        )
        def update_scenes_pie(table_data, tooltip_data, tables, chosen_dataset, population, optional):
            if not tables or not chosen_dataset or not population:
                return no_update

            batches_weight_case = Case(alias="batch_weight")
            for row, tooltip_row in list(zip(table_data, tooltip_data))[::-1]:
                condition = tooltip_row["batch_name"]["value"]
                curr_weight = row["weight"]
                batches_weight_case = batches_weight_case.when(LiteralValue(condition), curr_weight)

            page_filters: str = optional.get("page_filters", None)
            page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()
            tables: list[Base] = load_object(tables)

            data = self.weighted_scenes_query(
                chosen_dataset, tables, page_filters, batches_weight_case, self.scene_category
            )
            data = pd.melt(data, var_name="categories", value_name="weight")
            definitions_dict = {scene.name: scene.definition() for scene in self.scene_category.scenes}
            definitions_dict.update({"other": "non of the above"})
            data["definition"] = data["categories"].apply(lambda x: definitions_dict[x])
            fig = basic_pie_chart(data, "categories", "weight", title=self.title, hover="definition")
            return fig

    @staticmethod
    def weighted_scenes_query(
        chosen_dataset: str,
        tables: list[Base],
        page_filters: Criterion,
        batches_weight_case: Case,
        scenes: ScenesCategory,
    ) -> pd.DataFrame:
        tables = [table for table in tables if table.dataset_name == chosen_dataset]
        assert len(tables) == 1, f"Expected one table for dataset {chosen_dataset}, got {len(tables)}"
        base = base_data_subquery(
            main_tables=tables,
            meta_data_tables=tables,
            terms=list({*scenes.terms(), batches_weight_case}),
            page_filters=page_filters,
            to_order=False,
        )
        scenes_query = Query.from_(base).select(
            *scenes.weighted_sums(frame_weight=base.batch_weight, include_other=True)
        )
        data = execute(scenes_query)
        return data
