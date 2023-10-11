import dash_bootstrap_components as dbc
import numpy as np
from dash import html, dcc, register_page, Input, Output, callback, State, no_update, ALL

from road_eval_dashboard.components import (
    meta_data_filter,
    base_dataset_statistics,
    pathnet_data_filter,
)
from road_eval_dashboard.components.components_ids import (
    PATH_NET_ACC_HOST,
    PATH_NET_ACC_NEXT,
    PATH_NET_FALSES_HOST,
    PATH_NET_FALSES_NEXT,
    PATHNET_FILTERS,
    MD_FILTERS,
    NETS,
    PATH_NET_MISSES_NEXT,
    PATH_NET_MISSES_HOST,
    PATH_NET_ALL_CONF_MATS,
    PATH_NET_HOST_CONF_MAT,
    PATH_NET_OVERALL_CONF_MAT,
    PATH_NET_ALL_CONF_DIAGONAL,
    PATH_NET_HOST_CONF_DIAGONAL,
    PATHNET_PRED,
    PATHNET_GT,
)
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.components.queries_manager import (
    generate_path_net_query,
    distances,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper

from road_eval_dashboard.components.confusion_matrices_layout import generate_matrices_layout, generate_matrices_graphs

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/path_net", name="Path Net", order=9, **extra_properties.__dict__)

layout = html.Div(
    [
        html.H1("Path Net Metrics", className="mb-5"),
        meta_data_filter.layout,
        pathnet_data_filter.layout,
        base_dataset_statistics.dp_layout,
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=PATH_NET_ACC_HOST, config={"displayModeBar": False})]),
                            width=6,
                        ),
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=PATH_NET_ACC_NEXT, config={"displayModeBar": False})]),
                            width=6,
                        ),
                    ]
                )
            ]
        ),
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=PATH_NET_FALSES_HOST, config={"displayModeBar": False})]),
                            width=6,
                        ),
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=PATH_NET_FALSES_NEXT, config={"displayModeBar": False})]),
                            width=6,
                        ),
                    ]
                )
            ]
        ),
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=PATH_NET_MISSES_HOST, config={"displayModeBar": False})]),
                            width=6,
                        ),
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=PATH_NET_MISSES_NEXT, config={"displayModeBar": False})]),
                            width=6,
                        ),
                    ]
                )
            ]
        ),
        html.Div(
            id=PATH_NET_ALL_CONF_MATS,
        ),
    ]
)


@callback(
    Output(PATH_NET_ACC_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_path_net_acc_host(meta_data_filters, pathnet_filters, nets):
    if not nets:
        return no_update

    query = generate_path_net_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        "accuracy",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role="host",
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy", role="host")


@callback(
    Output(PATH_NET_ACC_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_path_net_acc_next(meta_data_filters, pathnet_filters, nets):
    if not nets:
        return no_update

    query = generate_path_net_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        "accuracy",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role="non-host"
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy")


@callback(
    Output(PATH_NET_FALSES_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_path_net_falses_host(meta_data_filters, pathnet_filters, nets):
    if not nets:
        return no_update

    query = generate_path_net_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        "falses",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role="host",
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "falses", role="host")


@callback(
    Output(PATH_NET_FALSES_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_path_net_falses_next(meta_data_filters, pathnet_filters, nets):
    if not nets:
        return no_update

    query = generate_path_net_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        "falses",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role="non-host"
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "falses")


@callback(
    Output(PATH_NET_MISSES_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_path_net_misses_host(meta_data_filters, pathnet_filters, nets):
    if not nets:
        return no_update

    query = generate_path_net_query(
        nets[PATHNET_GT],
        nets["meta_data"],
        "misses",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role="host"
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "misses", role="host")


@callback(
    Output(PATH_NET_MISSES_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_path_net_misses_next(meta_data_filters, pathnet_filters, nets):
    if not nets:
        return no_update

    query = generate_path_net_query(
        nets[PATHNET_GT],
        nets["meta_data"],
        "misses",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role="non-host"
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "misses", role="non-host")


@callback(
    Output(PATH_NET_ALL_CONF_MATS, "children"),
    Input(NETS, "data"),
)
def generate_matrices_components(nets):
    if not nets:
        return []

    children = generate_matrices_layout(
        nets=nets,
        overall_diag_id=PATH_NET_ALL_CONF_DIAGONAL,
        host_diag_id=PATH_NET_HOST_CONF_DIAGONAL,
        overall_conf_mat_id=PATH_NET_OVERALL_CONF_MAT,
        host_conf_mat_id=PATH_NET_HOST_CONF_MAT,
    )
    return children


@callback(
    Output(PATH_NET_ALL_CONF_DIAGONAL, "figure"),
    Output({"type": PATH_NET_OVERALL_CONF_MAT, "index": ALL}, "figure"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
)
def generate_overall_matrices(nets, meta_data_filters):
    if not nets:
        return no_update

    diagonal_compare, mats_figs = generate_matrices_graphs(
        label_col="split_role",
        pred_col="matched_split_role",
        nets_tables=nets[PATHNET_PRED],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=["NONE", "SPLIT_LEFT", "SPLIT_RIGHT", "IGNORE", "UNDEFINED"],
    )
    return diagonal_compare, mats_figs


@callback(
    Output(PATH_NET_HOST_CONF_DIAGONAL, "figure"),
    Output({"type": PATH_NET_HOST_CONF_MAT, "index": ALL}, "figure"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
)
def generate_host_matrices(nets, meta_data_filters):
    if not nets:
        return no_update

    diagonal_compare, mats_figs = generate_matrices_graphs(
        label_col="split_role",
        pred_col="matched_split_role",
        nets_tables=nets[PATHNET_PRED],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=["NONE", "SPLIT_LEFT", "SPLIT_RIGHT", "IGNORE", "UNDEFINED"],
    )

    return diagonal_compare, mats_figs
