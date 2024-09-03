from typing import List

import dash_bootstrap_components as dbc
from dash import html

from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_object import GridObject


def grid_layout(grid_objects: List[GridObject]):
    rows_objs = generate_obj_grid(grid_objects)
    generic_filters_charts = html.Div(
        [dbc.Row([dbc.Col(card_wrapper(obj.layout())) for obj in single_row_objs]) for single_row_objs in rows_objs]
    )
    return generic_filters_charts


def generate_obj_grid(graphs_properties: List[GridObject]) -> List[List[GridObject]]:
    obj_props = []
    curr_row = []
    for graph in graphs_properties:
        if graph.full_grid_row:
            obj_props.append([graph])
            continue

        curr_row.append(graph)
        if len(curr_row) == 2:
            obj_props.append(curr_row)
            curr_row = []

    if curr_row:
        obj_props.append(curr_row)

    return obj_props
