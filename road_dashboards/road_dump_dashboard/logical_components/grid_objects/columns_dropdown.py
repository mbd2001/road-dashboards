import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html, no_update
from pypika import Criterion

from road_dashboards.road_dump_dashboard.graphical_components.confusion_matrix import get_confusion_matrix
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.init_data_sources import EXISTING_TABLES
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import conf_mat_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import (
    execute,
    get_main_and_secondary_columns,
    load_object,
)


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
            value=None,
        )
        return columns_dropdown

    def _callbacks(self):
        pass
