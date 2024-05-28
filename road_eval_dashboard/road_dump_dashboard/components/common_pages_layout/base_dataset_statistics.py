import dash_bootstrap_components as dbc
from dash import html

from road_eval_dashboard.road_dump_dashboard.components.common_pages_layout import (
    intersection_data_switch,
    objs_count_card,
    population_card,
)


def layout(objs_name, main_table, meta_data_table=None):
    objs_layout = html.Div(
        dbc.Row(
            [
                dbc.Col(population_card.layout),
                dbc.Col(intersection_data_switch.layout),
                dbc.Col(objs_count_card.layout(objs_name, main_table, meta_data_table)),
            ]
        )
    )
    return objs_layout
