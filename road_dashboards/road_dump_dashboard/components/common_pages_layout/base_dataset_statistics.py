import dash_bootstrap_components as dbc
from dash import html

from road_dashboards.road_dump_dashboard.components.common_pages_layout import (
    intersection_data_switch,
    objs_count_card,
    population_card,
)

layout = html.Div(
    dbc.Row(
        [
            dbc.Col(objs_count_card.layout),
            dbc.Col(population_card.layout),
            dbc.Col(intersection_data_switch.layout),
        ]
    )
)
