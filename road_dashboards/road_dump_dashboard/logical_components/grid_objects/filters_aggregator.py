from functools import reduce
from operator import and_

from dash import Input, Output, callback, dcc
from pypika import EmptyCriterion

from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import dump_object, load_object


class FiltersAggregator(GridObject):
    def __init__(
        self,
        *args: str,
        component_id: str = "",
    ):
        self.inputs_ids = args
        super().__init__(full_grid_row=True, component_id=component_id)

    def _generate_ids(self):
        self.final_filter_id = self._generate_id("final_filter")

    def layout(self):
        return dcc.Store(self.final_filter_id, data=dump_object(EmptyCriterion()))

    def _callbacks(self):
        @callback(
            Output(self.final_filter_id, "data"),
            [Input(input_id, "data") for input_id in self.inputs_ids],
        )
        def generate_curr_filters(*args):
            args = [load_object(arg) for arg in args]
            return dump_object(reduce(and_, args))
