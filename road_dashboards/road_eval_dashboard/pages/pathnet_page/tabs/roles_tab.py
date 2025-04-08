import itertools
import json

import dash_bootstrap_components as dbc
from dash import ALL, MATCH, Input, Output, State, callback, dcc, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS,
    PATH_NET_ALL_CONF_MATS,
    PATH_NET_ALL_CONF_MATS_STORE,
    PATH_NET_ALL_TPR,
    PATH_NET_HOST_CONF_MAT,
    PATH_NET_HOST_CONF_MATS_STORE,
    PATH_NET_HOST_TPR,
    PATHNET_FILTERS,
    PATHNET_PRED,
)
from road_dashboards.road_eval_dashboard.components.confusion_matrices_layout import generate_conf_matrices
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_dashboards.road_eval_dashboard.graphs.confusion_matrix import draw_multiple_nets_confusion_matrix
from road_dashboards.road_eval_dashboard.graphs.tp_rate_graph import draw_conf_diagonal_compare
from road_dashboards.road_eval_dashboard.utils.consts import ROLE_IGNORE_VAL
from road_dashboards.road_eval_dashboard.utils.url_state_utils import create_dropdown_options_list

ROLE_CLASSES_NAMES = {
    "lane": ["NONE", "HOST", "NEXT_LEFT", "NEXT_RIGHT", "ONCOMING", "LANE_CHANGE", "IGNORE", "UNDEFINED"],
    "split": ["NONE", "SPLIT_LEFT", "SPLIT_RIGHT", "IGNORE"],
    "merge": ["NONE", "MERGE_LEFT", "MERGE_RIGHT", "IGNORE"],
    "primary": ["NONE", "PRIMARY", "SECONDARY", "IGNORE", "UNDEFINED"],
}

role_layout = html.Div([html.Div(id={"out": "graph", "role": role}) for role in ROLE_CLASSES_NAMES.keys()])


def generate_matrices_graphs(
    nets,
    role,
    meta_data_filters,
    pathnet_filters,
    mat_name,
):
    class_names = ROLE_CLASSES_NAMES[role]
    mats = generate_conf_matrices(
        label_col=f"matched_{role}_role",
        pred_col=f"{role}_role",
        nets_tables=nets[PATHNET_PRED],
        meta_data_table=nets["meta_data"],
        ignore_val=ROLE_IGNORE_VAL,
        meta_data_filters=meta_data_filters,
        class_names=class_names,
        extra_filters=pathnet_filters,
    )
    conf_mats = [mat["conf_matrix"] for mat in mats.values()]
    normalize_mats = [mat["normalize_mat"] for mat in mats.values()]
    net_names = list(mats.keys())
    diagonal_compare = draw_conf_diagonal_compare(normalize_mats, net_names, class_names, role=role, mat_name=mat_name)
    mats_figs = draw_multiple_nets_confusion_matrix(
        conf_mats, normalize_mats, net_names, class_names, role=role, mat_name=mat_name
    )
    serialized_mats_figs = {net_name: fig.to_plotly_json() for net_name, fig in zip(net_names, mats_figs)}
    return diagonal_compare, serialized_mats_figs


@callback(
    Output({"type": PATH_NET_ALL_TPR, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_ALL_CONF_MATS_STORE, "role": MATCH}, "data"),
    Output({"type": "net_options", "role": MATCH}, "options"),
    Output({"type": "net_options", "role": MATCH}, "value"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State({"type": PATH_NET_ALL_TPR, "role": MATCH}, "id"),
)
def generate_all_dps_data(nets, meta_data_filters, pathnet_filters, graph_id):
    if not nets:
        return no_update, no_update

    role = graph_id["role"]
    diagonal_compare, serialized_mats_figs = generate_matrices_graphs(
        nets,
        role,
        meta_data_filters,
        pathnet_filters,
        mat_name=f"{role} TPR for all dps",
    )
    nets_name_include_suffix = list(serialized_mats_figs.keys())
    net_options = create_dropdown_options_list(nets_name_include_suffix)
    default_value = nets_name_include_suffix[0]

    return diagonal_compare, json.dumps(serialized_mats_figs), net_options, default_value


@callback(
    Output({"type": PATH_NET_HOST_TPR, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_HOST_CONF_MATS_STORE, "role": MATCH}, "data"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State({"type": PATH_NET_ALL_TPR, "role": MATCH}, "id"),
)
def generate_host_data(nets, meta_data_filters, pathnet_filters, graph_id):
    if not nets or graph_id["role"] == "lane":
        return no_update, []

    role = graph_id["role"]
    pathnet_filters = f"{pathnet_filters} AND role = 'host'" if pathnet_filters else "role = 'host'"
    diagonal_compare, serialized_mats_figs = generate_matrices_graphs(
        nets,
        role,
        meta_data_filters,
        pathnet_filters,
        mat_name=f"{role} TPR for Host dps",
    )
    return diagonal_compare, json.dumps(serialized_mats_figs)


@callback(
    Output({"type": PATH_NET_ALL_CONF_MATS, "role": MATCH, "index": ALL}, "figure"),
    Output({"type": PATH_NET_HOST_CONF_MAT, "role": MATCH, "index": ALL}, "figure"),
    Input({"type": "net_options", "role": MATCH}, "value"),
    State({"type": PATH_NET_ALL_CONF_MATS_STORE, "role": MATCH}, "data"),
    State({"type": PATH_NET_HOST_CONF_MATS_STORE, "role": MATCH}, "data"),
)
def draw_conf_mat(chosen_net, all_dps_conf_mats_store, host_conf_mats_store):
    def load_conf_mat(conf_mats_store):
        if conf_mats_store is None:
            return []
        conf_mats_dict = json.loads(conf_mats_store)
        return [conf_mats_dict[chosen_net]]

    if not chosen_net:
        return no_update, no_update

    all_dps_conf_mat = load_conf_mat(all_dps_conf_mats_store)
    host_conf_mat = load_conf_mat(host_conf_mats_store)
    return all_dps_conf_mat, host_conf_mat


# ----------------------------------------------- layout creation ----------------------------------------------- #


@callback(
    Output({"out": "graph", "role": MATCH}, "children"),
    Input(NETS, "data"),
    State({"out": "graph", "role": MATCH}, "id"),
)
def generate_roles_layout(nets, graph_id):
    if not nets:
        return []

    all_dps_tpr_id = {"type": PATH_NET_ALL_TPR, "role": graph_id["role"]}
    host_tpr_id = {"type": PATH_NET_HOST_TPR, "role": graph_id["role"]}
    conf_mat_option_id = {"type": "net_options", "role": graph_id["role"]}
    all_dps_conf_mat_id = {"type": PATH_NET_ALL_CONF_MATS, "role": graph_id["role"], "index": 0}
    all_dps_conf_mats_store_id = {"type": PATH_NET_ALL_CONF_MATS_STORE, "role": graph_id["role"]}
    host_conf_mat_id = {"type": PATH_NET_HOST_CONF_MAT, "role": graph_id["role"], "index": 0}
    host_conf_mats_store_id = {"type": PATH_NET_HOST_CONF_MATS_STORE, "role": graph_id["role"]}

    create_host_graph = graph_id["role"] != "lane"

    tpr_graphs_ids = [all_dps_tpr_id]
    conf_mats_ids = [all_dps_conf_mat_id]
    if create_host_graph:
        tpr_graphs_ids.append(host_tpr_id)
        conf_mats_ids.append(host_conf_mat_id)

    roles_layout = [card_wrapper(loading_wrapper(graph_wrapper(tpr_graph_id))) for tpr_graph_id in tpr_graphs_ids]
    roles_layout.append(
        card_wrapper(
            [
                dbc.Row([html.H4("Confusion Matrix", style={"textAlign": "center"})]),
                dcc.Store(id=all_dps_conf_mats_store_id),
                dcc.Store(id=host_conf_mats_store_id),
                dbc.Row(loading_wrapper(dcc.Dropdown(id=conf_mat_option_id, placeholder="Select Net"))),
                dbc.Row([dbc.Col(graph_wrapper(conf_mat_id), width=6) for conf_mat_id in conf_mats_ids]),
            ]
        )
    )

    return roles_layout
