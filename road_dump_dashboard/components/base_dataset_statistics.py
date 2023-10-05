import dash_bootstrap_components as dbc
from dash import html

from road_dump_dashboard.components import (
    frame_count_card,
    population_card,
)


frame_layout = html.Div(
    dbc.Row(
        [
            dbc.Col(population_card.layout),
            dbc.Col(frame_count_card.layout),
        ]
    )
)
