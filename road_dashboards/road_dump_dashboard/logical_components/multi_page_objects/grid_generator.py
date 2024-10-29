import dash_bootstrap_components as dbc
from dash import html
from road_dump_dashboard.logical_components.constants.layout_wrappers import card_wrapper
from road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject


class GridGenerator(GridObject):
    def __init__(
        self,
        *grid_objects: GridObject,
        warp_sub_objects: bool = True,
        component_id: str = "",
    ):
        self.grid_objects = grid_objects
        self.warp_sub_objects = warp_sub_objects
        super().__init__(full_grid_row=True, component_id=component_id)

    def _generate_ids(self):
        pass

    def layout(self):
        rows_objs = self.generate_obj_grid(*self.grid_objects)
        grid_layout = [dbc.Row([dbc.Col(obj.layout()) for obj in single_row_objs]) for single_row_objs in rows_objs]
        if self.warp_sub_objects:
            grid_layout = card_wrapper(grid_layout)

        return html.Div(grid_layout, id=self.component_id, style={"display": "block"})

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
