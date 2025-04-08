import dash_bootstrap_components as dbc
import numpy as np
from dash import html

from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_conf_mat_query,
    process_net_name,
    process_net_names_list,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.confusion_matrix import (
    compute_confusion_matrix,
    draw_multiple_nets_confusion_matrix,
)
from road_dashboards.road_eval_dashboard.graphs.tp_rate_graph import draw_conf_diagonal_compare


def generate_matrices_layout(nets, upper_diag_id, lower_diag_id, left_conf_mat_id, right_conf_mat_id):
    if not nets:
        return []

    children = [
        card_wrapper(
            [
                loading_wrapper(
                    [
                        dbc.Row(
                            [
                                graph_wrapper(upper_diag_id),
                            ]
                        )
                    ]
                )
            ]
        ),
        card_wrapper(
            [
                loading_wrapper(
                    [
                        dbc.Row(
                            [
                                graph_wrapper(lower_diag_id),
                            ]
                        )
                    ]
                )
            ]
        ),
    ] + [
        generate_confusion_matrix_card_layout(net_name, ind, left_conf_mat_id, right_conf_mat_id)
        for ind, net_name in enumerate(process_net_names_list(nets["names"]))
    ]
    return children


def generate_confusion_matrix_card_layout(net, ind, left_conf_mat_id, right_conf_mat_id):
    left_conf_mat_id, right_conf_mat_id = add_indices(ind, left_conf_mat_id, right_conf_mat_id)
    layout = card_wrapper(
        [
            dbc.Row([html.H4(children=net, style={"textAlign": "center"})]),
            dbc.Row(
                [
                    dbc.Col(
                        graph_wrapper(left_conf_mat_id),
                        width=6,
                    ),
                    dbc.Col(
                        graph_wrapper(right_conf_mat_id),
                        width=6,
                    ),
                ],
            ),
        ]
    )
    return layout


def add_indices(ind, left_conf_mat_id, right_conf_mat_id):
    if type(left_conf_mat_id) == str:
        left_conf_mat_id = {"type": left_conf_mat_id}
    if type(right_conf_mat_id) == str:
        right_conf_mat_id = {"type": right_conf_mat_id}
    left_conf_mat_id.update({"index": ind})
    right_conf_mat_id.update({"index": ind})
    return left_conf_mat_id, right_conf_mat_id


def generate_conf_matrices(
    label_col,
    pred_col,
    nets_tables,
    meta_data_table,
    ignore_val,
    meta_data_filters="",
    role="",
    class_names=[],
    ca_oriented=False,
    compare_sign=False,
    extra_filters="",
):
    if extra_filters:
        extra_filters = f'{extra_filters} AND "{label_col}" != {ignore_val}'
    else:
        extra_filters = f'"{label_col}" != {ignore_val}'
    query = generate_conf_mat_query(
        nets_tables,
        meta_data_table,
        label_col,
        pred_col,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        role=role,
        ca_oriented=ca_oriented,
        compare_sign=compare_sign,
    )
    data, _ = run_query_with_nets_names_processing(query)
    mats = {}
    num_classes = len(class_names)
    net_names = set(data["net_id"].values)
    for net_name in net_names:
        net_id = process_net_name(net_name)
        net_data = data[data["net_id"] == net_id]
        conf_matrix, normalize_mat = compute_confusion_matrix(net_data, label_col, pred_col, num_classes)
        mats[net_id] = {"conf_matrix": conf_matrix, "normalize_mat": normalize_mat}
    return mats


def generate_matrices_graphs(
    label_col,
    pred_col,
    nets_tables,
    meta_data_table,
    net_names,
    ignore_val,
    meta_data_filters="",
    role="",
    mat_name="",
    class_names=[],
    ca_oriented=False,
    compare_sign=False,
    extra_filters="",
):
    mats = generate_conf_matrices(
        label_col,
        pred_col,
        nets_tables,
        meta_data_table,
        ignore_val=ignore_val,
        meta_data_filters=meta_data_filters,
        role=role,
        class_names=class_names,
        ca_oriented=ca_oriented,
        compare_sign=compare_sign,
        extra_filters=extra_filters,
    )
    conf_mats = [mat["conf_matrix"] for mat in mats.values()]
    normalize_mats = [mat["normalize_mat"] for mat in mats.values()]
    mats_figs = draw_multiple_nets_confusion_matrix(
        conf_mats,
        normalize_mats,
        net_names,
        class_names,
        role=role,
        mat_name=mat_name,
    )
    diagonal_compare = draw_conf_diagonal_compare(normalize_mats, net_names, class_names, role=role, mat_name=mat_name)
    return diagonal_compare, mats_figs


def generate_matrices_graphs_lr(
    label_col_template,
    pred_col_template,
    nets_tables,
    meta_data_table,
    time_value,
    ignore_val,
    meta_data_filters="",
    role="",
    class_names=[],
    ca_oriented=False,
    compare_sign=False,
    extra_filters="",
):
    """Generates conf matrix data for left, right, and combined 'all' sides."""

    results = {"left": {}, "right": {}, "all": {}}

    # Generate matrices for left side
    mats_left = generate_conf_matrices(
        label_col=f"{label_col_template}_left_{time_value}",
        pred_col=f"{pred_col_template}_left_{time_value}",
        nets_tables=nets_tables,
        meta_data_table=meta_data_table,
        ignore_val=ignore_val,
        meta_data_filters=meta_data_filters,
        role=role,
        class_names=class_names,
        extra_filters=extra_filters,
        ca_oriented=ca_oriented,
        compare_sign=compare_sign,
    )
    results["left"] = mats_left

    # Generate matrices for right side
    mats_right = generate_conf_matrices(
        label_col=f"{label_col_template}_right_{time_value}",
        pred_col=f"{pred_col_template}_right_{time_value}",
        nets_tables=nets_tables,
        meta_data_table=meta_data_table,
        ignore_val=ignore_val,
        meta_data_filters=meta_data_filters,
        role=role,
        class_names=class_names,
        extra_filters=extra_filters,
        ca_oriented=ca_oriented,
        compare_sign=compare_sign,
    )
    results["right"] = mats_right

    # Calculate combined 'all' matrix data
    num_classes = len(class_names)
    default_zero_mat = np.zeros((num_classes, num_classes))
    net_names = set(mats_left.keys()) | set(mats_right.keys())
    for net_name in net_names:
        conf_left = mats_left.get(net_name, {}).get("conf_matrix", default_zero_mat)
        conf_right = mats_right.get(net_name, {}).get("conf_matrix", default_zero_mat)
        combined_conf = conf_left + conf_right

        # Normalize the combined matrix
        row_sums = combined_conf.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        combined_norm = combined_conf / row_sums

        results["all"][net_name] = {"conf_matrix": combined_conf, "normalize_mat": combined_norm}

    return results
