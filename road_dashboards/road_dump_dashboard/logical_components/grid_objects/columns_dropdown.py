from dash import dcc

from road_dashboards.road_dump_dashboard.logical_components.constants.init_data_sources import EXISTING_TABLES
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject


class ColumnsDropdown(GridObject):
    def __init__(
        self,
        main_table: str,
        full_grid_row: bool = False,
        component_id: str = "",
    ):
        self.main_table = main_table
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        pass

    def layout(self):
        columns_dropdown = dcc.Dropdown(
            id=self.component_id,
            multi=False,
            placeholder="Attribute",
            options=EXISTING_TABLES[self.main_table].get_columns(),
            value="",
        )
        return columns_dropdown

    def _callbacks(self):
        pass
