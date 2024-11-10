import dash_bootstrap_components as dbc
from dash import ALL, MATCH, Input, Output, State, callback, html, no_update

from road_dashboards.road_eval_dashboard.components.common_filters import PATHNET_MISS_FALSE_FILTERS
from road_dashboards.road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS,
    PATH_NET_ALL_CONF_MATS,
    PATH_NET_ALL_TPR,
    PATH_NET_FALSES_NEXT,
    PATH_NET_HOST_CONF_MAT,
    PATH_NET_HOST_TPR,
    PATH_NET_MISSES_HOST,
    PATH_NET_MISSES_NEXT,
    PATHNET_FILTERS,
    PATHNET_PRED,
)
from road_dashboards.road_eval_dashboard.components.confusion_matrices_layout import generate_matrices_graphs
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper

ROLE_CLASSES_NAMES = {
    "split": ["NONE", "SPLIT_LEFT", "SPLIT_RIGHT", "IGNORE"],
    "merge": ["NONE", "MERGE_LEFT", "MERGE_RIGHT", "IGNORE"],
    "primary": ["NONE", "PRIMARY", "SECONDARY", "IGNORE", "UNDEFINED"],
}

role_layout = html.Div([html.Div(id={"out": "graph", "role": role}) for role in ["split", "merge", "primary"]])


@callback(
    Output({"type": PATH_NET_ALL_TPR, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_ALL_CONF_MATS, "role": MATCH, "index": ALL}, "figure"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
    State({"type": PATH_NET_ALL_TPR, "role": MATCH}, "id"),
    Input(PATHNET_FILTERS, "data"),
)
def generate_overall_conf_matrices(nets, meta_data_filters, graph_id, pathnet_filters):
    if not nets:
        return no_update
    role = graph_id["role"]
    diagonal_compare, mats_figs = generate_matrices_graphs(
        pred_col=f"{role}_role",
        label_col=f"matched_{role}_role",
        nets_tables=nets[PATHNET_PRED],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=ROLE_CLASSES_NAMES[role],
        mat_name=f"{role} TPR for all dps",
        extra_filters=pathnet_filters,
    )
    return diagonal_compare, mats_figs


@callback(
    Output({"type": PATH_NET_HOST_TPR, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_HOST_CONF_MAT, "index": ALL, "role": MATCH}, "figure"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
    State({"type": PATH_NET_ALL_TPR, "role": MATCH}, "id"),
    Input(PATHNET_FILTERS, "data"),
)
def generate_host_conf_matrices(nets, meta_data_filters, graph_id, pathnet_filters):
    if not nets:
        return no_update
    if pathnet_filters:
        pathnet_filters = f"{pathnet_filters} AND role = 'host'"
    else:
        pathnet_filters = "role = 'host'"
    role = graph_id["role"]
    diagonal_compare, mats_figs = generate_matrices_graphs(
        pred_col=f"{role}_role",
        label_col=f"matched_{role}_role",
        nets_tables=nets[PATHNET_PRED],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=ROLE_CLASSES_NAMES[role],
        mat_name=f"{role} TPR for host dp",
        extra_filters=pathnet_filters,
    )

    return diagonal_compare, mats_figs


def get_miss_false_layout():
    layout = []
    for p_filter in PATHNET_MISS_FALSE_FILTERS:
        layout += [
            card_wrapper(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                graph_wrapper({"id": PATH_NET_FALSES_NEXT, "filter": p_filter}),
                                width=4,
                            ),
                            dbc.Col(
                                graph_wrapper({"id": PATH_NET_MISSES_HOST, "filter": p_filter}),
                                width=4,
                            ),
                            dbc.Col(
                                graph_wrapper({"id": PATH_NET_MISSES_NEXT, "filter": p_filter}),
                                width=4,
                            ),
                        ]
                    ),
                ]
            ),
        ]
        return layout
