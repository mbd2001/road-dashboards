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


def generate_matrices_layout(nets, overall_diag_id, host_diag_id, overall_conf_mat_id, host_conf_mat_id):
    if not nets:
        return []

    children = [
        card_wrapper(
            [
                loading_wrapper(
                    [
                        dbc.Row(
                            [
                                dcc.Graph(id=overall_diag_id, config={"displayModeBar": False}),
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
                                dcc.Graph(id=host_diag_id, config={"displayModeBar": False}),
                            ]
                        )
                    ]
                )
            ]
        ),
    ] + [
        generate_confusion_matrix_card_layout(
            process_net_name(nets["names"][ind]), ind, overall_conf_mat_id, host_conf_mat_id
        )
        for ind in range(len(nets["names"]))
    ]
    return children


def generate_confusion_matrix_card_layout(net, ind, overall_conf_mat_id, host_conf_mat_id):
    layout = card_wrapper(
        [
            dbc.Row([html.H4(children=net, style={"textAlign": "center"})]),
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper(
                            [
                                dcc.Graph(
                                    id={"type": overall_conf_mat_id, "index": ind}, config={"displayModeBar": False}
                                )
                            ]
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        loading_wrapper(
                            [dcc.Graph(id={"type": host_conf_mat_id, "index": ind}, config={"displayModeBar": False})]
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
    host=False,
    class_names=[],
    pathnet_oriented=False,
):
    query = generate_conf_mat_query(
        nets_tables,
        meta_data_table,
        label_col,
        pred_col,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{label_col} != -1",
        host=host,
        pathnet_oriented=pathnet_oriented,
    )

    data, _ = run_query_with_nets_names_processing(query)
    mats_figs, normalize_mats = draw_multiple_nets_confusion_matrix(
        data, label_col, pred_col, net_names, class_names, host=host
    )
    diagonal_compare = draw_conf_diagonal_compare(normalize_mats, net_names, class_names, host=host)
    return diagonal_compare, mats_figs
