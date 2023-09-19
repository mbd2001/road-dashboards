import dash_bootstrap_components as dbc
from dash import html, dcc

from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components.queries_manager import (
    generate_conf_mat_query,
    run_query_with_nets_names_processing,
    process_net_name,
)
from road_eval_dashboard.graphs.confusion_matrix import draw_multiple_nets_confusion_matrix
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
        generate_confusion_matrix_card_layout(
            process_net_name(nets["names"][ind]), ind, left_conf_mat_id, right_conf_mat_id
        )
        for ind in range(len(nets["names"]))
    ]
    return children


def generate_confusion_matrix_card_layout(net, ind, left_conf_mat_id, right_conf_mat_id):
    layout = card_wrapper(
        [
            dbc.Row([html.H4(children=net, style={"textAlign": "center"})]),
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper(
                            [dcc.Graph(id={"type": left_conf_mat_id, "index": ind}, config={"displayModeBar": False})]
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        loading_wrapper(
                            [dcc.Graph(id={"type": right_conf_mat_id, "index": ind}, config={"displayModeBar": False})]
                        ),
                        width=6,
                    ),
                ],
            ),
        ]
    )
    return layout


def generate_matrices_graphs(
    label_col,
    pred_col,
    nets_tables,
    meta_data_table,
    net_names,
    meta_data_filters="",
    role="",
    conf_name="",
    class_names=[],
    ca_oriented=False,
    include_all=False,
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
        include_all=include_all,
        ca_oriented=ca_oriented,
        compare_sign=compare_sign,
    )
    data, _ = run_query_with_nets_names_processing(query)
    mats_figs, normalize_mats = draw_multiple_nets_confusion_matrix(
        data,
        label_col,
        pred_col,
        net_names,
        class_names,
        role=role,
        conf_name=conf_name,
    )
    diagonal_compare = draw_conf_diagonal_compare(
        normalize_mats, net_names, class_names, role=role, conf_name=conf_name
    )
    return diagonal_compare, mats_figs
