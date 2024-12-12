from functools import reduce
from operator import add

import pandas as pd
from dash import ALL, Input, Output, State, callback, dcc, no_update
from pypika import Case, Criterion, EmptyCriterion, Query, functions

from road_dashboards.road_dump_dashboard.graphical_components.pie_chart import basic_pie_chart
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
from road_dashboards.road_dump_dashboard.table_schemes.scenes import Scene


class ScenesPie(GridObject):
    def __init__(
        self,
        datasets_dropdown_id: str,
        population_dropdown_id: str,
        slider_id: str,
        scenes: list[Scene],
        page_filters_id: str = "",
        full_grid_row: bool = False,
        component_id: str = "",
    ):
        self.datasets_dropdown_id = datasets_dropdown_id
        self.population_dropdown_id = population_dropdown_id
        self.slider_id = slider_id
        self.scenes = scenes
        self.page_filters_id = page_filters_id
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

            data = self.weighted_scenes_query(chosen_dump, tables, page_filters, batches_weight_case, self.scenes)

            definitions_dict = {scene.name: str(scene.definition) for scene in self.scenes}
            definitions_dict.update({"other": "non of the above", "mixed": "combination of the above"})
            data["definition"] = data["categories"].apply(lambda x: definitions_dict[x])
            fig = basic_pie_chart(data, "categories", "weight", title="Scenes Distribution", hover="definition")
            return fig

    @staticmethod
    def weighted_scenes_query(
        chosen_dump: str,
        tables: list[Base],
        page_filters: Criterion,
        batches_weight_case: Case,
        scenes: list[Scene],
    ) -> pd.DataFrame:
        tables = [table for table in tables if table.dataset_name == chosen_dump]
        base_terms = [col for scene in scenes for col in scene.definition.find_(Column)]

        base = base_data_subquery(
            main_tables=tables,
            meta_data_tables=tables,
            terms=list({*base_terms, batches_weight_case}),
            page_filters=page_filters,
        )
        mixed_case = reduce(add, [Case().when(scene.definition, 1).else_(0) for scene in scenes]) > 1
        cases = Case("categories").when(mixed_case, "mixed")
        for scene in scenes:
            cases = cases.when(scene.definition, scene.name)

        cases = cases.else_("other")
        categories_query = Query.from_(base).select(base.batch_weight, cases)
        group_by_query = (
            Query.from_(categories_query)
            .select(categories_query.categories, functions.Sum(categories_query.batch_weight).as_("weight"))
            .groupby(categories_query.categories)
        )
        data = execute(group_by_query)
        return data
