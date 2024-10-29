import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import plotly.express as px
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    BOUNDARY_DROP_DOWN,
    MD_FILTERS,
    NETS,
    PATHNET_BOUNDARIES,
    PATHNET_BOUNDARY_ACC,
    PATHNET_DYNAMIC_THRESHOLD_BOUNDARIES,
    PATHNET_FILTERS,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    distances,
    generate_path_net_double_boundaries_query,
    generate_path_net_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph

boundaries_layout = html.Div(
    [
        dbc.Row(
            dcc.Dropdown(
                options=[
                    {"label": "All boundaries", "value": "all"},
                    {"label": "only left boundaries", "value": "left"},
                    {"label": "only right boundaries", "value": "right"},
                ],
                value="all",
                id=BOUNDARY_DROP_DOWN,
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    graph_wrapper({"id": PATHNET_BOUNDARY_ACC, "role": "host"}),
                    width=6,
                ),
                dbc.Col(
                    graph_wrapper({"id": PATHNET_BOUNDARY_ACC, "role": "non-host"}),
                    width=6,
                ),
            ]
        ),
        dbc.Row(
            [
                html.Label("acc-threshold (m)", style={"text-align": "center", "fontSize": "20px"}),
                dcc.RangeSlider(
                    id="boundaries-acc-threshold-slider", min=0, max=2, step=0.1, value=[0.2, 0.5], allowCross=False
                ),
            ]
        ),
    ]
)


@callback(Output(PATHNET_DYNAMIC_THRESHOLD_BOUNDARIES, "data"), Input("boundaries-acc-threshold-slider", "value"))
def compute_dynamic_distances_dict(slider_values):
    coeff = np.polyfit([1.3, 3], slider_values, deg=1)
    threshold_polynomial = np.poly1d(coeff)
    distances_dict = {sec: max(threshold_polynomial(sec), 0.2) for sec in distances}
    return distances_dict


@callback(
    Output({"id": PATHNET_BOUNDARY_ACC, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    State({"id": PATHNET_BOUNDARY_ACC, "role": MATCH}, "id"),
    Input(PATHNET_DYNAMIC_THRESHOLD_BOUNDARIES, "data"),
    Input(BOUNDARY_DROP_DOWN, "value"),
)
def get_path_net_acc_next(meta_data_filters, pathnet_filters, nets, graph_id, distances_dict, drop_down_value):
    if not nets:
        return no_update
    role = graph_id["role"]
    if drop_down_value == "all":
        query = generate_path_net_double_boundaries_query(
            nets[PATHNET_BOUNDARIES],
            nets["meta_data"],
            distances_dict,
            meta_data_filters,
            extra_filters=pathnet_filters,
            extra_columns=None,
            role=role,
            base_dist_column_name=f"dist",
        )
    else:
        query = generate_path_net_query(
            nets[PATHNET_BOUNDARIES],
            nets["meta_data"],
            distances_dict,
            meta_data_filters,
            extra_filters=pathnet_filters,
            extra_columns=None,
            role=role,
            base_dist_column_name=f"dist_{drop_down_value}",
        )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, title=f"{role} boundary", yaxis="% accurate dps", role="")
