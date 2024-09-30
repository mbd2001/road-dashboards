import dash_bootstrap_components as dbc
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS,
    PATH_NET_QUALITY_FN,
    PATH_NET_QUALITY_FP,
    PATH_NET_QUALITY_TN,
    PATH_NET_QUALITY_TP,
    PATH_NET_QUALITY_UNMATHCED_CORRECT_REJECTION,
    PATHNET_PRED,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    distances,
    generate_path_net_dp_quality_query,
    generate_path_net_dp_quality_true_rejection_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph
from road_dashboards.road_eval_dashboard.utils.colors import GREEN, RED

quality_layout = html.Div(
    [
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            graph_wrapper({"type": PATH_NET_QUALITY_UNMATHCED_CORRECT_REJECTION, "role": "host"}),
                            width=6,
                        ),
                        dbc.Col(
                            graph_wrapper({"type": PATH_NET_QUALITY_UNMATHCED_CORRECT_REJECTION, "role": "non-host"}),
                            width=6,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_TP, "role": "host"}), width=6),
                        dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_TP, "role": "non-host"}), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_TN, "role": "host"}), width=6),
                        dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_TN, "role": "non-host"}), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_FP, "role": "host"}), width=6),
                        dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_FP, "role": "non-host"}), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_FN, "role": "host"}), width=6),
                        dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_FN, "role": "non-host"}), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        html.Label("quality-threshold (score)", style={"text-align": "center", "fontSize": "20px"}),
                        dcc.RangeSlider(
                            id="quality-threshold-slider", min=-3, max=3, step=0.1, value=[0], allowCross=False
                        ),
                    ]
                ),
            ]
        )
    ]
)


@callback(
    Output({"type": PATH_NET_QUALITY_TP, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
    State({"type": PATH_NET_QUALITY_TP, "role": MATCH}, "id"),
)
def get_path_net_quality_score_tp(meta_data_filters, nets, slider_values, idx):
    if not nets:
        return no_update

    acc_dist_operator = "<"
    quality_operator = ">"

    role = idx["role"]
    query = generate_path_net_dp_quality_query(
        data_tables=nets[PATHNET_PRED],
        meta_data=nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role=role,
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df, cols=distances, title="DPs Quality Score - TP", role=role, yaxis="% hit", plot_bgcolor=GREEN
    )
    return fig


@callback(
    Output({"type": PATH_NET_QUALITY_TN, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
    State({"type": PATH_NET_QUALITY_TN, "role": MATCH}, "id"),
)
def get_path_net_quality_score_tn(meta_data_filters, nets, slider_values, idx):
    if not nets:
        return no_update

    acc_dist_operator = ">"
    quality_operator = "<="
    role = idx["role"]

    query = generate_path_net_dp_quality_query(
        data_tables=nets[PATHNET_PRED],
        meta_data=nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role=role,
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df,
        cols=distances,
        title="DPs Quality Score - TN",
        role=role,
        yaxis="% correct rejection",
        plot_bgcolor=GREEN,
    )
    return fig


@callback(
    Output({"type": PATH_NET_QUALITY_FP, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
    State({"type": PATH_NET_QUALITY_FP, "role": MATCH}, "id"),
)
def get_path_net_quality_score_fp(meta_data_filters, nets, slider_values, idx):
    if not nets:
        return no_update

    acc_dist_operator = "<"
    quality_operator = "<="
    role = idx["role"]

    query = generate_path_net_dp_quality_query(
        data_tables=nets[PATHNET_PRED],
        meta_data=nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role=role,
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df, cols=distances, title="DPs Quality Score - FP", role=role, yaxis="% false alarm", plot_bgcolor=RED
    )
    return fig


@callback(
    Output({"type": PATH_NET_QUALITY_FN, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
    State({"type": PATH_NET_QUALITY_FN, "role": MATCH}, "id"),
)
def get_path_net_quality_score_fn(meta_data_filters, nets, slider_values, idx):
    if not nets:
        return no_update

    acc_dist_operator = ">"
    quality_operator = ">"
    role = idx["role"]

    query = generate_path_net_dp_quality_query(
        data_tables=nets[PATHNET_PRED],
        meta_data=nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role=role,
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df, cols=distances, title="DPs Quality Score - FN", role=role, yaxis="% miss", plot_bgcolor=RED
    )
    return fig


@callback(
    Output({"type": PATH_NET_QUALITY_UNMATHCED_CORRECT_REJECTION, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
    State({"type": PATH_NET_QUALITY_UNMATHCED_CORRECT_REJECTION, "role": MATCH}, "id"),
)
def get_path_net_quality_score_unmatched_correct_rejection(meta_data_filters, nets, slider_values, idx):
    if not nets:
        return no_update

    acc_dist_operator = ">"
    quality_operator = "<"
    role = idx["role"]

    query = generate_path_net_dp_quality_true_rejection_query(
        data_tables=nets[PATHNET_PRED],
        meta_data=nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role=[f"'{role}'", f"'unmatched-{role}'"],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df,
        cols=distances,
        title="DPs Quality - Unmatched Corrcert Rejection",
        role=role,
        yaxis="% correct rejection",
        plot_bgcolor=GREEN,
    )
    return fig
