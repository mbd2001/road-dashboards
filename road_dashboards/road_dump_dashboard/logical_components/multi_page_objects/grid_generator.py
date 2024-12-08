import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component

from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import card_wrapper
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject


class GridGenerator(GridObject):
    def __init__(
        self,
        *grid_objects: GridObject | Component,
        warp_sub_objects: bool = True,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.grid_objects = grid_objects
        self.warp_sub_objects = warp_sub_objects
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        pass

    def layout(self):
        rows_objs = self.generate_obj_grid(*self.grid_objects)
        grid_layout = [
            dbc.Row([obj if isinstance(obj, Component) else dbc.Col(obj.layout()) for obj in single_row_objs])
            for single_row_objs in rows_objs
        ]
        if self.warp_sub_objects:
            grid_layout = card_wrapper(grid_layout)

        return html.Div(grid_layout, id=self.component_id, hidden=False)

    def _callbacks(self):
        pass

    @staticmethod
    def generate_obj_grid(*grid_objects: GridObject | Component) -> list[list[GridObject | Component]]:
        obj_props: list[list[GridObject | Component]] = []
        curr_row: list[GridObject | Component] = []

        def add_current_row_and_reset():
            nonlocal obj_props
            nonlocal curr_row

            obj_props.append(curr_row)
            curr_row = []

        for obj in grid_objects:
            if isinstance(obj, Component) or obj.full_grid_row:
                if curr_row:
                    add_current_row_and_reset()

                curr_row.append(obj)
                add_current_row_and_reset()
                continue

            curr_row.append(obj)
            if len(curr_row) == 2:
                add_current_row_and_reset()

        if curr_row:
            add_current_row_and_reset()

        return obj_props
