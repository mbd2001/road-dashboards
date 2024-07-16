from typing import Callable, List

import dash_bootstrap_components as dbc
from dash import html

from road_dashboards.road_dump_dashboard.components.constants.graphs_properties import BaseGraphProperties
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper


def get_grid_layout(graphs_properties: List[BaseGraphProperties], single_graph_func: Callable):
    obj_props = generate_obj_grid(graphs_properties)
    generic_filters_charts = html.Div(
        [
            dbc.Row([dbc.Col(card_wrapper(single_graph_func(obj_prop))) for obj_prop in obj_props_in_row])
            for obj_props_in_row in obj_props
        ]
    )
    return generic_filters_charts


def generate_obj_grid(graphs_properties: List[BaseGraphProperties]):
    obj_props = []
    curr_row = []
    for graph in graphs_properties:
        if graph.full_grid_row is True:
            obj_props.append([graph])
            continue

        curr_row.append(graph)
        if len(curr_row) == 2:
            obj_props.append(curr_row)
            curr_row = []

    if curr_row:
        obj_props.append(curr_row)

    return obj_props
