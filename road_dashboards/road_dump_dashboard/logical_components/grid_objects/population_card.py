from dash import Input, Output, callback, dcc, html
from pypika import EmptyCriterion

from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import dump_object
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class PopulationCard(GridObject):
    POPULATIONS = ["train", "test"]

    def __init__(
        self,
        populations: list[str] | None = None,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.populations = populations if populations else self.POPULATIONS
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.populations_dropdown_id = self._generate_id("populations_dropdown")
        self.final_filter_id = self._generate_id("final_filter")

    def layout(self):
        population_layout = [
            dcc.Store(self.final_filter_id, data=dump_object(EmptyCriterion())),
            dcc.Dropdown(
                options={population: population.title() for population in self.populations},
                value=self.populations[0],
                id=self.populations_dropdown_id,
                multi=False,
                placeholder="----",
            ),
        ]
        return population_layout

    def _callbacks(self):
        @callback(
            Output(self.final_filter_id, "data"),
            Input(self.populations_dropdown_id, "value"),
        )
        def generate_curr_filters(population):
            population_filter = MetaData.population == population
            return dump_object(population_filter)
