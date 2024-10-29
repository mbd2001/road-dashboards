from dash import Input, Output, callback, dcc, no_update
from road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject

from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import load_object


class DatasetsSelector(GridObject):
    def __init__(
        self,
        main_table: str,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.main_table: str = main_table
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.main_dataset_dropdown_id: str = self._generate_id("main_net_dropdown")

    def layout(self):
        selector_layout = dcc.Dropdown(
            id=self.main_dataset_dropdown_id,
            style={"minWidth": "100%"},
            multi=False,
            placeholder="----",
            value="",
        )
        return selector_layout

    def _callbacks(self):
        @callback(
            Output(self.main_dataset_dropdown_id, "options"),
            Output(self.main_dataset_dropdown_id, "label"),
            Output(self.main_dataset_dropdown_id, "value"),
            Input(self.main_table, "data"),
        )
        def init_main_dropdown(main_tables):
            if not main_tables:
                return no_update, no_update, no_update

            main_tables: list[Base] = load_object(main_tables)
            options = {table.dataset_name: table.dataset_name.title() for table in main_tables}
            return options, main_tables[0].dataset_name.title(), main_tables[0].dataset_name
