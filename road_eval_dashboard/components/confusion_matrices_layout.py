import dash_bootstrap_components as dbc
from dash import dcc, html

from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components.queries_manager import (
    generate_conf_mat_query,
    process_net_name,
    process_net_names_list,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.graphs.confusion_matrix import compute_confusion_matrix, draw_multiple_nets_confusion_matrix
from road_eval_dashboard.graphs.tp_rate_graph import draw_conf_diagonal_compare


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
                                dcc.Graph(id=upper_diag_id, config={"displayModeBar": False}),
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
                                dcc.Graph(id=lower_diag_id, config={"displayModeBar": False}),
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
    if type(left_conf_mat_id) == str:
        left_conf_mat_id = {"type": left_conf_mat_id}
    if type(right_conf_mat_id) == str:
        right_conf_mat_id = {"type": right_conf_mat_id}
    left_conf_mat_id.update({"index": ind})
    right_conf_mat_id.update({"index": ind})
    print(left_conf_mat_id,"\n", right_conf_mat_id)
    layout = card_wrapper(
        [
            dbc.Row([html.H4(children=net, style={"textAlign": "center"})]),
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper(
                            [dcc.Graph(id=left_conf_mat_id, config={"displayModeBar": False})]
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        loading_wrapper(
                            [dcc.Graph(id=right_conf_mat_id, config={"displayModeBar": False})]
                        ),
                        width=6,
                    ),
                ],
            ),
        ]
    )
    return layout


def generate_conf_matrices(
    label_col,
    pred_col,
    nets_tables,
    meta_data_table,
    net_names,
    meta_data_filters="",
    role="",
    mat_name="",
    class_names=[],
    ca_oriented=False,
    compare_sign=False,
    ignore_val=-1,
):
    query = generate_conf_mat_query(
        nets_tables,
        meta_data_table,
        label_col,
        pred_col,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{label_col} != {ignore_val}",
        role=role,
        ca_oriented=ca_oriented,
        compare_sign=compare_sign,
    )
    data, _ = run_query_with_nets_names_processing(query)
    mats = {}
    num_classes = len(class_names)
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
    meta_data_filters="",
    role="",
    mat_name="",
    class_names=[],
    ca_oriented=False,
    compare_sign=False,
    ignore_val=-1,
):
    net_names = process_net_names_list(net_names)
    mats = generate_conf_matrices(
        label_col,
        pred_col,
        nets_tables,
        meta_data_table,
        net_names,
        meta_data_filters=meta_data_filters,
        role=role,
        mat_name=mat_name,
        class_names=class_names,
        ca_oriented=ca_oriented,
        compare_sign=compare_sign,
        ignore_val=ignore_val,
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
