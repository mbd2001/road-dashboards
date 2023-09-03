import dash_bootstrap_components as dbc
from dash import html

from road_eval_dashboard.components import (
    frame_count_card,
    gt_count_card,
    dp_count_card,
    emdp_count_card,
    population_card,
)


gt_layout = html.Div(
    dbc.Row(
        [
            dbc.Col(population_card.layout),
            dbc.Col(frame_count_card.layout),
            dbc.Col(gt_count_card.layout),
        ]
    )
)


dp_layout = html.Div(
    dbc.Row(
        [
            dbc.Col(population_card.layout),
            dbc.Col(frame_count_card.layout),
            dbc.Col(dp_count_card.layout),
        ]
    )
)


frame_layout = html.Div(
    dbc.Row(
        [
            dbc.Col(population_card.layout),
            dbc.Col(frame_count_card.layout),
            dbc.Col(emdp_count_card.layout),
        ]
    )
)
