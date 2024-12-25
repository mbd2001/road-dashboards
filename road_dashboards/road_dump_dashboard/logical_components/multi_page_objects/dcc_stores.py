from dash import dcc, html
from dash.development.base_component import Component

from road_dashboards.road_dump_dashboard.logical_components.constants.init_data_sources import EXISTING_TABLES


def init_dcc_stores() -> Component:
    return html.Div([dcc.Store(id=table, data=None) for table in EXISTING_TABLES])
