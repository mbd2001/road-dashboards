import json

import dash_bootstrap_components as dbc
import numpy as np
from dash import ALL, MATCH, Input, Output, State, callback, dcc, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    BOUNDARIES_ALL_CONF_MATS,
    BOUNDARIES_ALL_DIAG_COMPARE,
    BOUNDARIES_ALL_MATRICES_LR_STORE,
    BOUNDARIES_HOST_CONF_MATS,
    BOUNDARIES_HOST_DIAG_COMPARE,
    BOUNDARIES_HOST_MATRICES_LR_STORE,
    BOUNDARY_DROP_DOWN,
    MD_FILTERS,
    NETS,
    PATHNET_BOUNDARIES,
    PATHNET_BOUNDARY_ACC,
    PATHNET_DYNAMIC_THRESHOLD_BOUNDARIES,
    PATHNET_FILTERS,
    PATHNET_RE_ACC,
    RE_DROP_DOWN,
)
from road_dashboards.road_eval_dashboard.components.confusion_matrices_layout import (
    draw_conf_diagonal_compare,
    draw_multiple_nets_confusion_matrix,
    generate_matrices_graphs_lr,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_path_net_double_boundaries_query,
    generate_path_net_query,
    process_net_name,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph
from road_dashboards.road_eval_dashboard.utils.consts import BOUNDARY_IGNORE_VAL, BOUNDARY_TYPES_NAMES
from road_dashboards.road_eval_dashboard.utils.distances import SECONDS, compute_distances_dict
from road_dashboards.road_eval_dashboard.utils.url_state_utils import create_dropdown_options_list

BOUNDARY_ONTOLOGIES = ["boundaries"]
ONTOLOGY_CLASSES_NAMES = {"boundaries": BOUNDARY_TYPES_NAMES}
EMPTY_FIGURE = {"data": [], "layout": {}}


def get_ontology_column_templates(ontology, gt_pred):
    if gt_pred == "gt" or gt_pred == "label":
        return f"{ontology}_gt_type"
    elif gt_pred == "pred" or gt_pred == "prediction":
        return f"{ontology}_type"
    else:
        raise ValueError(f"Unknown gt_pred value: {gt_pred}")


def get_boundaries_layout(dropdown_id, graph_id, slider_id):
    return card_wrapper(
        [
            dbc.Row(
                dcc.Dropdown(
                    options=[
                        {"label": "All boundaries", "value": "all"},
                        {"label": "only left boundaries", "value": "left"},
                        {"label": "only right boundaries", "value": "right"},
                    ],
                    value="all",
                    id=dropdown_id,
                )
            ),
            dbc.Row(
                [
                    dbc.Col(
                        graph_wrapper({"id": graph_id, "role": "host"}),
                        width=6,
                    ),
                    dbc.Col(
                        graph_wrapper({"id": graph_id, "role": "non-host"}),
                        width=6,
                    ),
                ]
            ),
            dbc.Row(
                [
                    html.Label("acc-threshold (m)", style={"text-align": "center", "fontSize": "20px"}),
                    dcc.Slider(
                        id=slider_id,
                        min=0,
                        max=2,
                        step=0.1,
                        value=0.5,
                    ),
                ]
            ),
        ]
    )


boundaries_layout = html.Div(
    [
        get_boundaries_layout(BOUNDARY_DROP_DOWN, PATHNET_BOUNDARY_ACC, "boundaries-acc-threshold-slider"),
        get_boundaries_layout(RE_DROP_DOWN, PATHNET_RE_ACC, "res-acc-threshold-slider"),
    ]
    + [html.Div(id={"out": "graph", "bound": bo}) for bo in BOUNDARY_ONTOLOGIES]
)


def serialize_lr_data(lr_all_data):
    """Serializes the nested dictionary containing numpy arrays from generate_matrices_graphs_lr."""
    serializable = {}
    for side, net_data in lr_all_data.items():
        serializable[side] = {}
        for net_id, matrix_data in net_data.items():
            serializable[side][net_id] = {
                "conf_matrix": matrix_data["conf_matrix"].tolist()
                if isinstance(matrix_data.get("conf_matrix"), np.ndarray)
                else matrix_data.get("conf_matrix"),
                "normalize_mat": matrix_data["normalize_mat"].tolist()
                if isinstance(matrix_data.get("normalize_mat"), np.ndarray)
                else matrix_data.get("normalize_mat"),
            }
    return json.dumps(serializable)


def deserialize_lr_data(json_data):
    """Deserializes the L/R/All data back into dicts with numpy arrays."""
    if not json_data:
        return {"left": {}, "right": {}, "all": {}}
    loaded_data = json.loads(json_data)
    deserialized = {}
    for side, net_data in loaded_data.items():
        deserialized[side] = {}
        for net_id, matrix_data in net_data.items():
            deserialized[side][net_id] = {
                "conf_matrix": np.array(matrix_data["conf_matrix"])
                if matrix_data.get("conf_matrix") is not None
                else None,
                "normalize_mat": np.array(matrix_data["normalize_mat"])
                if matrix_data.get("normalize_mat") is not None
                else None,
            }
    return deserialized


@callback(
    Output({"type": BOUNDARIES_ALL_MATRICES_LR_STORE, "bound": MATCH}, "data"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input("boundaries-time-slider", "value"),
    State({"type": BOUNDARIES_ALL_MATRICES_LR_STORE, "bound": MATCH}, "id"),
)
def update_all_lr_store(nets, meta_data_filters, pathnet_filters, time_value, store_id):
    if not nets:
        return json.dumps({"left": {}, "right": {}, "all": {}})

    bound = store_id["bound"]

    lr_all_data = generate_matrices_graphs_lr(
        label_col_template=get_ontology_column_templates(bound, "gt"),
        pred_col_template=get_ontology_column_templates(bound, "pred"),
        nets_tables=nets[PATHNET_BOUNDARIES],
        meta_data_table=nets["meta_data"],
        time_value=f"{time_value:.1f}",
        ignore_val=BOUNDARY_IGNORE_VAL,
        meta_data_filters=meta_data_filters,
        role="",
        class_names=ONTOLOGY_CLASSES_NAMES[bound],
        extra_filters=pathnet_filters,
    )
    return serialize_lr_data(lr_all_data)


@callback(
    Output({"type": BOUNDARIES_HOST_MATRICES_LR_STORE, "bound": MATCH}, "data"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input("boundaries-time-slider", "value"),
    State({"type": BOUNDARIES_HOST_MATRICES_LR_STORE, "bound": MATCH}, "id"),
)
def update_host_lr_store(nets, meta_data_filters, pathnet_filters, time_value, store_id):
    if not nets:
        return json.dumps({"left": {}, "right": {}, "all": {}})

    bound = store_id["bound"]

    lr_all_data = generate_matrices_graphs_lr(
        label_col_template=get_ontology_column_templates(bound, "gt"),
        pred_col_template=get_ontology_column_templates(bound, "pred"),
        nets_tables=nets[PATHNET_BOUNDARIES],
        meta_data_table=nets["meta_data"],
        time_value=f"{time_value:.1f}",
        ignore_val=BOUNDARY_IGNORE_VAL,
        meta_data_filters=meta_data_filters,
        role="host",
        class_names=ONTOLOGY_CLASSES_NAMES[bound],
        extra_filters="",
    )
    return serialize_lr_data(lr_all_data)


@callback(
    Output({"type": BOUNDARIES_ALL_DIAG_COMPARE, "bound": MATCH}, "figure"),
    Input("boundaries-side-dropdown", "value"),
    Input("boundaries-time-slider", "value"),
    Input({"type": BOUNDARIES_ALL_MATRICES_LR_STORE, "bound": MATCH}, "data"),
    State({"type": BOUNDARIES_ALL_DIAG_COMPARE, "bound": MATCH}, "id"),
)
def generate_all_dps_figures(side, time_value, lr_all_store_data, graph_id):
    role = ""
    role_str_acc = "all dps"
    bound = graph_id["bound"]
    class_names = ONTOLOGY_CLASSES_NAMES[bound]

    if not lr_all_store_data:
        return EMPTY_FIGURE

    lr_all_data = deserialize_lr_data(lr_all_store_data)
    net_names = list(lr_all_data.get("all", {}).keys())

    if side not in lr_all_data:
        return EMPTY_FIGURE

    selected_side_data = lr_all_data[side]

    default_zeros = np.zeros((len(class_names), len(class_names)))
    normalize_mats_for_drawing = [
        selected_side_data.get(net, {}).get("normalize_mat", default_zeros) for net in net_names
    ]

    mat_title = f"Per-Class Accuracy for {role_str_acc} ({side}, t={time_value:.1f}s)"

    diagonal_compare_fig = draw_conf_diagonal_compare(
        normalize_mats_for_drawing, net_names, class_names, role=role, mat_name=mat_title
    )

    return diagonal_compare_fig


@callback(
    Output({"type": BOUNDARIES_HOST_DIAG_COMPARE, "bound": MATCH}, "figure"),
    Input("boundaries-side-dropdown", "value"),
    Input("boundaries-time-slider", "value"),
    Input({"type": BOUNDARIES_HOST_MATRICES_LR_STORE, "bound": MATCH}, "data"),
    State({"type": BOUNDARIES_HOST_DIAG_COMPARE, "bound": MATCH}, "id"),
)
def generate_host_figures(side, time_value, lr_all_store_data, graph_id):
    role = "host"
    role_str_acc = "Host dps"
    bound = graph_id["bound"]
    class_names = ONTOLOGY_CLASSES_NAMES[bound]

    if not lr_all_store_data:
        return EMPTY_FIGURE

    lr_all_data = deserialize_lr_data(lr_all_store_data)
    net_names = list(lr_all_data.get("all", {}).keys())
    if side not in lr_all_data:
        return EMPTY_FIGURE

    selected_side_data = lr_all_data[side]

    default_zeros = np.zeros((len(class_names), len(class_names)))
    normalize_mats_for_drawing = [
        selected_side_data.get(net, {}).get("normalize_mat", default_zeros) for net in net_names
    ]

    mat_title = f"Per-Class Accuracy for {role_str_acc} ({side}, t={time_value:.1f}s)"

    diagonal_compare_fig = draw_conf_diagonal_compare(
        normalize_mats_for_drawing, net_names, class_names, role=role, mat_name=mat_title
    )

    return diagonal_compare_fig


@callback(
    Output({"type": BOUNDARIES_ALL_CONF_MATS, "bound": MATCH, "index": 0}, "figure"),
    Output({"type": BOUNDARIES_ALL_CONF_MATS, "bound": MATCH, "index": 1}, "figure"),
    Output({"type": BOUNDARIES_HOST_CONF_MATS, "bound": MATCH, "index": 0}, "figure"),
    Output({"type": BOUNDARIES_HOST_CONF_MATS, "bound": MATCH, "index": 1}, "figure"),
    Input({"type": "net_options", "bound": MATCH, "index": 1}, "value"),
    Input({"type": "net_options", "bound": MATCH, "index": 2}, "value"),
    Input("boundaries-side-dropdown", "value"),
    Input("boundaries-time-slider", "value"),
    Input({"type": BOUNDARIES_ALL_MATRICES_LR_STORE, "bound": MATCH}, "data"),
    Input({"type": BOUNDARIES_HOST_MATRICES_LR_STORE, "bound": MATCH}, "data"),
    State({"type": BOUNDARIES_ALL_CONF_MATS, "bound": MATCH, "index": ALL}, "id"),
)
def draw_conf_mat(net1_name, net2_name, side, time_value, all_lr_store_data, host_lr_store_data, graph_ids):
    if not all_lr_store_data or not host_lr_store_data:
        return EMPTY_FIGURE, EMPTY_FIGURE, EMPTY_FIGURE, EMPTY_FIGURE

    bound = graph_ids[0]["bound"]
    class_names = ONTOLOGY_CLASSES_NAMES[bound]

    empty_fig = EMPTY_FIGURE
    default_zeros = np.zeros((len(class_names), len(class_names)))

    def get_matrix_data(lr_data_store, selected_side, net_name):
        if not lr_data_store or not net_name:
            return default_zeros, default_zeros

        deserialized_data = deserialize_lr_data(lr_data_store)

        if selected_side not in deserialized_data:
            return default_zeros, default_zeros

        side_data = deserialized_data[selected_side]
        net_matrix_data = side_data.get(process_net_name(net_name), {})

        conf_mat = net_matrix_data.get("conf_matrix", default_zeros)
        norm_mat = net_matrix_data.get("normalize_mat", default_zeros)

        conf_mat = default_zeros if conf_mat is None else conf_mat
        norm_mat = default_zeros if norm_mat is None else norm_mat

        return conf_mat, norm_mat

    role_all = ""
    role_str_conf_all = "all dps"
    conf_mat_title_all = f"Confusion Matrix for {role_str_conf_all} ({side}, t={time_value:.1f}s)"

    conf_all_1, norm_all_1 = get_matrix_data(all_lr_store_data, side, net1_name)
    conf_all_2, norm_all_2 = get_matrix_data(all_lr_store_data, side, net2_name)

    fig_all_1 = (
        draw_multiple_nets_confusion_matrix(
            [conf_all_1],
            [norm_all_1],
            [net1_name or "None"],
            class_names,
            role=role_all,
            mat_name=conf_mat_title_all,
        )[0]
        if net1_name
        else empty_fig
    )
    fig_all_2 = (
        draw_multiple_nets_confusion_matrix(
            [conf_all_2],
            [norm_all_2],
            [net2_name or "None"],
            class_names,
            role=role_all,
            mat_name=conf_mat_title_all,
        )[0]
        if net2_name
        else empty_fig
    )

    role_host = "host"
    role_str_conf_host = "Host dps"
    conf_mat_title_host = f"Confusion Matrix for {role_str_conf_host} ({side}, t={time_value:.1f}s)"

    conf_host_1, norm_host_1 = get_matrix_data(host_lr_store_data, side, net1_name)
    conf_host_2, norm_host_2 = get_matrix_data(host_lr_store_data, side, net2_name)

    fig_host_1 = (
        draw_multiple_nets_confusion_matrix(
            [conf_host_1],
            [norm_host_1],
            [net1_name or "None"],
            class_names,
            role=role_host,
            mat_name=conf_mat_title_host,
        )[0]
        if net1_name
        else empty_fig
    )
    fig_host_2 = (
        draw_multiple_nets_confusion_matrix(
            [conf_host_2],
            [norm_host_2],
            [net2_name or "None"],
            class_names,
            role=role_host,
            mat_name=conf_mat_title_host,
        )[0]
        if net2_name
        else empty_fig
    )

    return fig_all_1, fig_all_2, fig_host_1, fig_host_2


@callback(
    Output({"out": "graph", "bound": MATCH}, "children"),
    Input(NETS, "data"),
    State({"out": "graph", "bound": MATCH}, "id"),
)
def generate_boundaries_layout(nets, graph_id):
    if not nets:
        return []

    bound = graph_id["bound"]

    all_dps_diag_compare_id = {"type": BOUNDARIES_ALL_DIAG_COMPARE, "bound": bound}
    host_diag_compare_id = {"type": BOUNDARIES_HOST_DIAG_COMPARE, "bound": bound}
    conf_mat_option_id_1 = {"type": "net_options", "bound": bound, "index": 1}
    conf_mat_option_id_2 = {"type": "net_options", "bound": bound, "index": 2}
    all_dps_conf_mat_id_1 = {"type": BOUNDARIES_ALL_CONF_MATS, "bound": bound, "index": 0}
    all_dps_conf_mat_id_2 = {"type": BOUNDARIES_ALL_CONF_MATS, "bound": bound, "index": 1}
    host_conf_mat_id_1 = {"type": BOUNDARIES_HOST_CONF_MATS, "bound": bound, "index": 0}
    host_conf_mat_id_2 = {"type": BOUNDARIES_HOST_CONF_MATS, "bound": bound, "index": 1}
    all_lr_store_id = {"type": BOUNDARIES_ALL_MATRICES_LR_STORE, "bound": bound}
    host_lr_store_id = {"type": BOUNDARIES_HOST_MATRICES_LR_STORE, "bound": bound}

    diag_compare_graphs_layout = card_wrapper(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H6(f"All DP Per-Class Accuracy for {bound}", style={"textAlign": "center"}),
                            loading_wrapper(graph_wrapper(all_dps_diag_compare_id)),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.H6(f"Host DP Per-Class Accuracy for {bound}", style={"textAlign": "center"}),
                            loading_wrapper(graph_wrapper(host_diag_compare_id)),
                        ],
                        width=6,
                    ),
                ]
            )
        ]
    )

    controls_layout = card_wrapper(
        [
            dbc.Row([html.H4(f"Confusion Matrix Comparison for {bound}", style={"textAlign": "center"})]),
            dcc.Store(id=all_lr_store_id),
            dcc.Store(id=host_lr_store_id),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Time horizon (seconds)", style={"text-align": "center", "fontSize": "20px"}),
                            dcc.Slider(
                                id="boundaries-time-slider",
                                min=min(SECONDS),
                                max=max(SECONDS),
                                value=0.5,
                                marks={float(s): str(s) for s in SECONDS},
                                step=float(SECONDS[1] - SECONDS[0]),
                            ),
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            html.Label("Boundary Side", style={"text-align": "center", "fontSize": "20px"}),
                            dcc.Dropdown(
                                id="boundaries-side-dropdown",
                                options=[
                                    {"label": "Both Boundaries", "value": "all"},
                                    {"label": "Left Boundary", "value": "left"},
                                    {"label": "Right Boundary", "value": "right"},
                                ],
                                value="all",
                                clearable=False,
                            ),
                        ],
                        width=4,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Network 1", style={"text-align": "center", "fontSize": "20px"}),
                            dcc.Dropdown(id=conf_mat_option_id_1, placeholder="Select First Net"),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Network 2", style={"text-align": "center", "fontSize": "20px"}),
                            dcc.Dropdown(id=conf_mat_option_id_2, placeholder="Select Second Net"),
                        ],
                        width=6,
                    ),
                ]
            ),
        ]
    )

    confusion_matrices_layout = card_wrapper(
        [
            dbc.Row(
                html.H5(
                    f"All Data Points Confusion Matrices for {bound}",
                    style={"textAlign": "center", "marginTop": "10px"},
                )
            ),
            dbc.Row(
                [
                    dbc.Col(loading_wrapper(graph_wrapper(all_dps_conf_mat_id_1)), width=6),
                    dbc.Col(
                        loading_wrapper(graph_wrapper(all_dps_conf_mat_id_2)),
                        width=6,
                        style={"borderLeft": "1px solid #ccc"},
                    ),
                ]
            ),
            dbc.Row(
                html.H5(
                    f"Host Data Points Confusion Matrices for {bound}",
                    style={"textAlign": "center", "marginTop": "20px"},
                )
            ),
            dbc.Row(
                [
                    dbc.Col(loading_wrapper(graph_wrapper(host_conf_mat_id_1)), width=6),
                    dbc.Col(
                        loading_wrapper(graph_wrapper(host_conf_mat_id_2)),
                        width=6,
                        style={"borderLeft": "1px solid #ccc"},
                    ),
                ]
            ),
        ]
    )

    return [controls_layout, confusion_matrices_layout, diag_compare_graphs_layout]


@callback(Output(PATHNET_DYNAMIC_THRESHOLD_BOUNDARIES, "data"), Input("boundaries-acc-threshold-slider", "value"))
def compute_dynamic_distances_dict(slider_value):
    if slider_value is None:
        return None
    # Create a dictionary mapping each second to the threshold value
    return {sec: slider_value for sec in SECONDS}


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
            base_dist_column_name="boundaries_dist",
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
            base_dist_column_name=f"boundaries_dist_{drop_down_value}",
        )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, SECONDS, title=f"{role} boundary", yaxis="% accurate dps", role="")


@callback(
    Output({"id": PATHNET_RE_ACC, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    State({"id": PATHNET_RE_ACC, "role": MATCH}, "id"),
    Input(PATHNET_DYNAMIC_THRESHOLD_BOUNDARIES, "data"),
    Input(RE_DROP_DOWN, "value"),
)
def get_path_net_acc_next_re(meta_data_filters, pathnet_filters, nets, graph_id, distances_dict, drop_down_value):
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
            base_dist_column_name="road_edges_dist",
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
            base_dist_column_name=f"road_edges_dist_{drop_down_value}",
        )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, SECONDS, title=f"{role} road-edge", yaxis="% accurate dps", role="")


@callback(
    Output({"type": "net_options", "bound": MATCH, "index": ALL}, "options"),
    Output({"type": "net_options", "bound": MATCH, "index": ALL}, "value"),
    Input({"type": BOUNDARIES_ALL_MATRICES_LR_STORE, "bound": MATCH}, "data"),
    State({"type": "net_options", "bound": MATCH, "index": ALL}, "id"),
)
def update_net_options(all_lr_store_data, dropdown_ids):
    num_dropdowns = len(dropdown_ids)
    empty_options = [[]] * num_dropdowns
    empty_values = [None] * num_dropdowns

    if not all_lr_store_data or not dropdown_ids:
        return empty_options, empty_values

    deserialized_data = deserialize_lr_data(all_lr_store_data)
    nets_names = list(deserialized_data.get("all", {}).keys())

    if not nets_names:
        return empty_options, empty_values

    none_option = {"label": "None", "value": ""}
    net_options = [none_option] + create_dropdown_options_list(nets_names)

    default_value_1 = nets_names[0] if nets_names else ""
    default_value_2 = "" if len(nets_names) <= 1 else ""

    default_values = [default_value_1, default_value_2]

    num_dropdowns = len(dropdown_ids)
    final_options = [net_options] * num_dropdowns
    final_values = default_values[:num_dropdowns] + [None] * (num_dropdowns - len(default_values))

    return final_options, final_values
