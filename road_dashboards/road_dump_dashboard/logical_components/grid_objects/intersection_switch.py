import dash_daq as daq

from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject


class IntersectionSwitch(GridObject):
    def __init__(
        self,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        pass

    def layout(self):
        switch_layout = daq.BooleanSwitch(
            id=self.component_id,
            on=False,
            label="Intersection",
            labelPosition="top",
        )
        return switch_layout

    def _callbacks(self):
        pass
