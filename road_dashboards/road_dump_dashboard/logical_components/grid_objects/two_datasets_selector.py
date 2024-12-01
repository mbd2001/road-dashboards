import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, no_update

from road_dashboards.road_dump_dashboard.logical_components.grid_objects.dataset_selector import DatasetSelector
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import load_object


class TwoDatasetsSelector(DatasetSelector):
    def __init__(
        self,
        main_table: str,
        obj_to_hide_ids: list[str] = None,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.obj_to_hide_ids: list[str] = obj_to_hide_ids if obj_to_hide_ids else []
        super().__init__(main_table=main_table, full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        super()._generate_ids()
        self.secondary_dataset_dropdown_id: str = self._generate_id("secondary_net_dropdown")

    def layout(self):
        nets_selection = dbc.Row(
            [
                dbc.Col(super().layout()),
                dbc.Col(
                    dcc.Dropdown(
                        id=self.secondary_dataset_dropdown_id,
                        multi=False,
                        placeholder="----",
                        value=None,
                    )
                ),
            ]
        )
        return nets_selection

    def _callbacks(self):
        super()._callbacks()

        @callback(
            Output(self.secondary_dataset_dropdown_id, "options"),
            Output(self.secondary_dataset_dropdown_id, "label"),
            Output(self.secondary_dataset_dropdown_id, "value"),
            Input(self.main_dataset_dropdown_id, "value"),
            Input(self.main_dataset_dropdown_id, "options"),
        )
        def init_secondary_dropdown(selected_val, options):
            if not selected_val:
                return no_update

            options = [val for val in options if val != selected_val]
            if not options:
                return no_update, no_update, no_update

            return options, options[0], options[0]

        for obj_to_hide_id in self.obj_to_hide_ids:

            @callback(
                Output(obj_to_hide_id, "hidden"),
                Input(self.main_table, "data"),
            )
            def toggle_hidden(main_tables):
                if not main_tables:
                    return no_update

                main_tables: list[Base] = load_object(main_tables)
                if len(main_tables) < 2:
                    return True

                return False
