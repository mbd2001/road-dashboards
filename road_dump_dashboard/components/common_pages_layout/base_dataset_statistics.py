import dash_bootstrap_components as dbc
from dash import html

from road_dump_dashboard.components.common_pages_layout import (
    frame_count_card,
    lm_count_card,
    intersection_data_switch,
    population_card,
)

frame_layout = html.Div(
    dbc.Row(
        [
            dbc.Col(population_card.layout),
            dbc.Col(intersection_data_switch.layout),
            dbc.Col(frame_count_card.layout),
        ]
    )
)


lm_layout = html.Div(
    dbc.Row(
        [
            dbc.Col(population_card.layout),
            dbc.Col(intersection_data_switch.layout),
            dbc.Col(lm_count_card.layout),
        ]
    )
)
