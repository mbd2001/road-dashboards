import dash_bootstrap_components as dbc
from dash import html

from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.layout_wrappers import card_wrapper


class GridGenerator(GridObject):
    def __init__(
        self,
        *grid_objects: GridObject,
        component_id: str = "",
    ):
        self.grid_objects = grid_objects
        super().__init__(full_grid_row=True, component_id=component_id)

    def _generate_ids(self):
        pass

    def layout(self):
        rows_objs = self.generate_obj_grid(*self.grid_objects)
        generic_filters_charts = html.Div(
            [dbc.Row([dbc.Col(card_wrapper(obj.layout())) for obj in single_row_objs]) for single_row_objs in rows_objs]
        )
        return generic_filters_charts

    def _callbacks(self):
        pass

    @staticmethod
    def generate_obj_grid(*grid_objects: GridObject) -> list[list[GridObject]]:
        obj_props = []
        curr_row = []
        for graph in grid_objects:
            if graph.full_grid_row:
                obj_props.append([graph])
                continue

            curr_row.append(graph)
            if len(curr_row) == 2:
                obj_props.append(curr_row)
                curr_row = []

        if curr_row:
            obj_props.append(curr_row)

        return obj_props
