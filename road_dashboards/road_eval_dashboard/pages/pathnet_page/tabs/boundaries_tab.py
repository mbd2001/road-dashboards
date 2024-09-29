import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import plotly.express as px
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    PATHNET_RIGHT_BOUNDARY_ACC,
    PATHNET_LEFT_BOUNDARY_ACC, NETS, PATHNET_FILTERS, MD_FILTERS, PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD,
    PATHNET_BOUNDARIES)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import generate_path_net_query, \
    run_query_with_nets_names_processing, distances
from road_dashboards.road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph

boundaries_layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    graph_wrapper({"id": PATHNET_LEFT_BOUNDARY_ACC, "side": "left"}),
                    width=6,
                ),
                dbc.Col(
                    graph_wrapper({"id": PATHNET_RIGHT_BOUNDARY_ACC, "side": "right"}),
                    width=6,
                ),
            ]
        )
    ]
)


@callback(
    Output({"id": PATHNET_LEFT_BOUNDARY_ACC, "side": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    State({"id": PATHNET_LEFT_BOUNDARY_ACC, "side": MATCH}, "id"),
    Input(PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, "data"),
)
def get_path_net_acc_next(meta_data_filters, pathnet_filters, nets, distances_dict, graph_id):
    if not nets:
        return no_update
    side = graph_id['side']
    query = generate_path_net_query(
        nets[PATHNET_BOUNDARIES],
        nets["meta_data"],
        distances_dict,
        meta_data_filters,
        extra_filters=pathnet_filters,
        role="",
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy", yaxis="% accurate dps")