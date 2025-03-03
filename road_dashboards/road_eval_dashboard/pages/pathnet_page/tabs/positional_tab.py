import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import plotly.express as px
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_eval_dashboard.components.common_filters import (
    PATHNET_BATCH_BY_SEC_FILTERS,
    PATHNET_MISS_FALSE_FILTERS,
)
from road_dashboards.road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS,
    PATH_NET_ACC_ALL_PRED,
    PATH_NET_ACC_HOST,
    PATH_NET_ACC_NEXT,
    PATH_NET_ALL_CONF_MATS,
    PATH_NET_ALL_TPR,
    PATH_NET_BIASES_HOST,
    PATH_NET_BIASES_NEXT,
    PATH_NET_FALSES_NEXT,
    PATH_NET_HOST_CONF_MAT,
    PATH_NET_HOST_TPR,
    PATH_NET_MISSES_HOST,
    PATH_NET_MISSES_NEXT,
    PATH_NET_MONOTONE_ACC_HOST,
    PATH_NET_MONOTONE_ACC_NEXT,
    PATH_NET_OOL,
    PATH_NET_OOL_BORDER_DIST_SLIDER,
    PATH_NET_OOL_RE_DIST_SLIDER,
    PATH_NET_SCENE_ACC_HOST,
    PATH_NET_SCENE_ACC_NEXT,
    PATH_NET_VIEW_RANGES_HOST,
    PATH_NET_VIEW_RANGES_NEXT,
    PATHNET_BOUNDARIES,
    PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD,
    PATHNET_DYNAMIC_THRESHOLD_OOL,
    PATHNET_DYNAMIC_THRESHOLD_RE_OOL,
    PATHNET_FILTERS,
    PATHNET_GT,
    PATHNET_INCLUDE_MATCHED_HOST,
    PATHNET_INCLUDE_MATCHED_NON_HOST,
    PATHNET_PRED,
)
from road_dashboards.road_eval_dashboard.components.confusion_matrices_layout import generate_matrices_layout
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_dashboards.road_eval_dashboard.components.pathnet_events_extractor.layout import (
    layout as events_extractor_card,
)
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    PATHNET_ACC_THRESHOLDS,
    distances,
    generate_count_query,
    generate_path_net_miss_false_query,
    generate_path_net_query,
    generate_path_net_scene_by_sec_query,
    generate_pathnet_cumulative_query,
    get_in_lane_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters
from road_dashboards.road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph


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


def get_cumulative_acc_layout():
    layout = []
    default_sec = [0.5, 3.5]
    for i in range(2):
        layout.append(
            card_wrapper(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                graph_wrapper({"id": PATH_NET_MONOTONE_ACC_HOST, "ind": i}),
                                width=6,
                            ),
                            dbc.Col(
                                graph_wrapper({"id": PATH_NET_MONOTONE_ACC_NEXT, "ind": i}),
                                width=6,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            html.Label(
                                "dist (sec)",
                                id={"id": "acc threshold", "ind": i},
                                style={"text-align": "center", "fontSize": "20px"},
                            ),
                            dcc.RangeSlider(
                                id={"id": "dist-column-slider", "ind": i},
                                min=0.5,
                                max=5,
                                step=0.5,
                                value=[default_sec[i]],
                            ),
                        ]
                    ),
                ]
            )
        )
    return layout


def get_acc_by_sec_layout():
    layout = []
    default_sec_slider = 1.5
    default_threshold_slider = [0.2, 0.5]
    for p_filter in PATHNET_BATCH_BY_SEC_FILTERS:
        layout += [
            card_wrapper(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                graph_wrapper({"id": PATH_NET_SCENE_ACC_HOST, "filter": p_filter}),
                                width=6,
                            ),
                            dbc.Col(
                                graph_wrapper({"id": PATH_NET_SCENE_ACC_NEXT, "filter": p_filter}),
                                width=6,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            html.Label(
                                "sec",
                                id={"id": "sec acc"},
                                style={"text-align": "center", "fontSize": "20px"},
                            ),
                            dcc.RangeSlider(
                                id={"id": "sec-slider", "filter": p_filter},
                                min=0.5,
                                max=5,
                                step=0.5,
                                value=[default_sec_slider],
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            html.Label("acc-threshold (m)", style={"text-align": "center", "fontSize": "20px"}),
                            dcc.RangeSlider(
                                id="acc-threshold-sliders",
                                min=0,
                                max=2,
                                step=0.1,
                                value=default_threshold_slider,
                                allowCross=False,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                daq.BooleanSwitch(
                                    id=PATHNET_INCLUDE_MATCHED_HOST,
                                    on=False,
                                    label="Filter Unmatched <-> Show All (include miss)",
                                    labelPosition="top",
                                )
                            ),
                            dbc.Col(
                                daq.BooleanSwitch(
                                    id=PATHNET_INCLUDE_MATCHED_NON_HOST,
                                    on=False,
                                    label="Filter Unmatched <-> Show All (include miss)",
                                    labelPosition="top",
                                )
                            ),
                        ]
                    ),
                ]
            )
        ]
    return layout


pos_layout = html.Div(
    [
        events_extractor_card,
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            graph_wrapper(PATH_NET_ACC_HOST),
                            width=4,
                        ),
                        dbc.Col(
                            graph_wrapper(PATH_NET_ACC_NEXT),
                            width=4,
                        ),
                        dbc.Col(
                            graph_wrapper(PATH_NET_ACC_ALL_PRED),
                            width=4,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        html.Label("acc-threshold (m)", style={"text-align": "center", "fontSize": "20px"}),
                        dcc.RangeSlider(
                            id="acc-threshold-slider", min=0, max=2, step=0.1, value=[0.2, 0.5], allowCross=False
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            daq.BooleanSwitch(
                                id=PATHNET_INCLUDE_MATCHED_HOST,
                                on=False,
                                label="Filter Unmatched <-> Show All (include miss)",
                                labelPosition="top",
                            )
                        ),
                        dbc.Col(
                            daq.BooleanSwitch(
                                id=PATHNET_INCLUDE_MATCHED_NON_HOST,
                                on=False,
                                label="Filter Unmatched <-> Show All (include miss)",
                                labelPosition="top",
                            )
                        ),
                        dbc.Col(
                            daq.BooleanSwitch(
                                id="include-unmatched-pred",
                                on=False,
                                label="Filter Unmatched <-> Show All (include false)",
                                labelPosition="top",
                            )
                        ),
                    ]
                ),
            ]
        ),
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(graph_wrapper({"id": PATH_NET_OOL, "role": "host"}), width=6),
                        dbc.Col(graph_wrapper({"id": PATH_NET_OOL, "role": "non-host"}), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        html.Label(
                            "minimum distance between dp and border (m)",
                            style={"text-align": "center", "fontSize": "20px"},
                        ),
                        dcc.RangeSlider(id=PATH_NET_OOL_BORDER_DIST_SLIDER, min=0, max=2, step=0.1, value=[0.8, 1]),
                    ]
                ),
                dbc.Row(
                    [
                        html.Label(
                            "minimum distance between dp and road-edge (m)",
                            style={"text-align": "center", "fontSize": "20px"},
                        ),
                        dcc.RangeSlider(id=PATH_NET_OOL_RE_DIST_SLIDER, min=0, max=2, step=0.1, value=[1, 1.2]),
                    ]
                ),
            ]
        ),
    ]
    + get_cumulative_acc_layout()
    + get_miss_false_layout()
    + get_acc_by_sec_layout()
    + [
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=PATH_NET_BIASES_HOST, config={"displayModeBar": False})]),
                            width=3,
                        ),
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=PATH_NET_BIASES_NEXT, config={"displayModeBar": False})]),
                            width=3,
                        ),
                        dbc.Col(
                            loading_wrapper(
                                [dcc.Graph(id=PATH_NET_VIEW_RANGES_HOST, config={"displayModeBar": False})]
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            loading_wrapper(
                                [dcc.Graph(id=PATH_NET_VIEW_RANGES_NEXT, config={"displayModeBar": False})]
                            ),
                            width=3,
                        ),
                    ]
                )
            ]
        ),
    ]
)


def compute_dynamic_distances_dict(slider_values):
    coeff = np.polyfit([1.3, 3], slider_values, deg=1)
    threshold_polynomial = np.poly1d(coeff)
    distances_dict = {sec: max(threshold_polynomial(sec), 0.2) for sec in distances}
    return distances_dict


@callback(
    Output(PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, "data"),
    Input("acc-threshold-slider", "value"),
)
def compute_acc_threshold_distances_dict(slider_values):
    return compute_dynamic_distances_dict(slider_values)


@callback(
    Output(PATHNET_DYNAMIC_THRESHOLD_OOL, "data"),
    Input(PATH_NET_OOL_BORDER_DIST_SLIDER, "value"),
)
def compute_ool_threshold_distances_dict(slider_values):
    return compute_dynamic_distances_dict([slider_values[1], slider_values[0]])


@callback(
    Output(PATHNET_DYNAMIC_THRESHOLD_RE_OOL, "data"),
    Input(PATH_NET_OOL_RE_DIST_SLIDER, "value"),
)
def compute_re_ool_threshold_distances_dict(slider_values):
    return compute_dynamic_distances_dict([slider_values[1], slider_values[0]])


@callback(
    Output(PATH_NET_ACC_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input(PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, "data"),
    Input(PATHNET_INCLUDE_MATCHED_HOST, "on"),
)
def get_path_net_acc_host(meta_data_filters, pathnet_filters, nets, distances_dict, include_unmatched):
    if not nets:
        return no_update
    if include_unmatched:
        role = ["'host'", "'unmatched-host'"]
    else:
        role = "host"
    query = generate_path_net_query(
        nets[PATHNET_GT],
        nets["meta_data"],
        distances_dict,
        meta_data_filters,
        extra_filters=pathnet_filters,
        role=role,
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy", role="host", yaxis="% accurate dps")


@callback(
    Output(PATH_NET_ACC_ALL_PRED, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input(PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, "data"),
    Input("include-unmatched-pred", "on"),
)
def get_path_net_acc_pred(meta_data_filters, pathnet_filters, nets, distances_dict, include_unmatched):
    if not nets:
        return no_update
    if include_unmatched:
        role = ["'host'", "'non-host'", "'unmatched-non-host'", "'unmatched-host'"]
    else:
        role = ["'host'", "'non-host'"]
    query = generate_path_net_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        distances_dict,
        meta_data_filters,
        extra_filters=pathnet_filters,
        role=role,
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy", role="Pred", yaxis="% accurate dps")


@callback(
    Output({"id": PATH_NET_MONOTONE_ACC_HOST, "ind": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input({"id": "dist-column-slider", "ind": MATCH}, "value"),
)
def get_path_net_monotone_acc_host(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update
    query = generate_pathnet_cumulative_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        f"dist_{float(slider_values[0])}",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role="host",
    )
    df, _ = run_query_with_nets_names_processing(query)
    rename_dict = {"precision_" + str(i): PATHNET_ACC_THRESHOLDS[i] for i in range(len(PATHNET_ACC_THRESHOLDS))}
    df.rename(columns=rename_dict, inplace=True)
    return draw_path_net_graph(
        df,
        list(df.columns)[1:],
        "Accuracy cumulative",
        score_func=score_func,
        xaxis="Thresholds (m)",
        role="host",
        yaxis="% accurate dps",
    )


def score_func(row, score_filter):
    return row[score_filter]


@callback(
    Output({"id": PATH_NET_MONOTONE_ACC_NEXT, "ind": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input({"id": "dist-column-slider", "ind": MATCH}, "value"),
)
def get_path_net_monotone_acc_next(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update
    query = generate_pathnet_cumulative_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        f"dist_{float(slider_values[0])}",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role="non-host",
    )
    df, _ = run_query_with_nets_names_processing(query)
    rename_dict = {"precision_" + str(i): PATHNET_ACC_THRESHOLDS[i] for i in range(len(PATHNET_ACC_THRESHOLDS))}
    df.rename(columns=rename_dict, inplace=True)
    return draw_path_net_graph(
        df,
        list(df.columns)[1:],
        "Accuracy cumulative",
        score_func=score_func,
        xaxis="Thresholds (m)",
        yaxis="% accurate dps",
    )


@callback(
    Output(PATH_NET_ACC_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input(PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, "data"),
    Input(PATHNET_INCLUDE_MATCHED_NON_HOST, "on"),
)
def get_path_net_acc_next(meta_data_filters, pathnet_filters, nets, distances_dict, include_unmatched):
    if not nets:
        return no_update
    if include_unmatched:
        role = ["'non-host'", "'unmatched-non-host'"]
    else:
        role = "non-host"
    query = generate_path_net_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        distances_dict,
        meta_data_filters,
        extra_filters=pathnet_filters,
        role=role,
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy", yaxis="% accurate dps")


@callback(
    Output({"id": PATH_NET_FALSES_NEXT, "filter": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    State({"id": PATH_NET_FALSES_NEXT, "filter": MATCH}, "id"),
)
def get_path_net_falses_next(meta_data_filters, pathnet_filters, nets, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    query = generate_path_net_miss_false_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        PATHNET_MISS_FALSE_FILTERS[filter_name],
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role=["'non-host'", "'unmatched-non-host'"],
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_meta_data_filters(
        df,
        title="<b>Falses<b>",
        yaxis="False rate",
        xaxis="",
        interesting_columns=list(PATHNET_MISS_FALSE_FILTERS[filter_name].keys()),
        interesting_filters=list(PATHNET_MISS_FALSE_FILTERS[filter_name].values()),
        score_func=lambda row, score_filter: row[f"score_{score_filter}"],
        hover=True,
        count_items_name="dps",
    )


@callback(
    Output({"id": PATH_NET_MISSES_HOST, "filter": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    State({"id": PATH_NET_MISSES_HOST, "filter": MATCH}, "id"),
)
def get_path_net_misses_host(meta_data_filters, pathnet_filters, nets, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    query = generate_path_net_miss_false_query(
        nets[PATHNET_GT],
        nets["meta_data"],
        PATHNET_MISS_FALSE_FILTERS[filter_name],
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role=["'host'", "'unmatched-host'"],
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_meta_data_filters(
        df,
        title="<b>Miss Host<b>",
        yaxis="Miss rate",
        xaxis="",
        interesting_columns=list(PATHNET_MISS_FALSE_FILTERS[filter_name].keys()),
        interesting_filters=list(PATHNET_MISS_FALSE_FILTERS[filter_name].values()),
        score_func=lambda row, score_filter: row[f"score_{score_filter}"],
        hover=True,
        count_items_name="dps",
    )


@callback(
    Output({"id": PATH_NET_SCENE_ACC_HOST, "filter": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input({"id": "sec-slider", "filter": MATCH}, "value"),
    Input(PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, "data"),
    Input(PATHNET_INCLUDE_MATCHED_HOST, "on"),
    State({"id": PATH_NET_SCENE_ACC_HOST, "filter": MATCH}, "id"),
)
def get_path_net_scene_sec_acc(
    meta_data_filters, pathnet_filters, nets, slider_values, distances_dict, include_unmatched, graph_id
):
    if not nets:
        return no_update
    if include_unmatched:
        role = ["'host'", "'unmatched-host'"]
    else:
        role = "host"
    filter_name = graph_id["filter"]
    sv = float(slider_values[0])
    query = generate_path_net_scene_by_sec_query(
        nets[PATHNET_GT],
        nets["meta_data"],
        {sv: distances_dict[str(sv)]},
        interesting_filters=PATHNET_BATCH_BY_SEC_FILTERS[filter_name],
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role=role,
    )

    df, _ = run_query_with_nets_names_processing(query)
    return draw_meta_data_filters(
        df,
        title=f"<b>Host {filter_name} Scene Accuracy<b>",
        yaxis="Acc rate",
        xaxis="",
        interesting_columns=list(PATHNET_BATCH_BY_SEC_FILTERS[filter_name].keys()),
        interesting_filters=list(PATHNET_BATCH_BY_SEC_FILTERS[filter_name].values()),
        score_func=lambda row, score_filter: row[f"score_{score_filter}"],
        hover=True,
        count_items_name="dps",
    )


@callback(
    Output({"id": PATH_NET_SCENE_ACC_NEXT, "filter": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input({"id": "sec-slider", "filter": MATCH}, "value"),
    Input(PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, "data"),
    Input(PATHNET_INCLUDE_MATCHED_NON_HOST, "on"),
    State({"id": PATH_NET_SCENE_ACC_NEXT, "filter": MATCH}, "id"),
)
def get_path_net_scene_sec_acc(
    meta_data_filters, pathnet_filters, nets, slider_values, distances_dict, include_unmatched, graph_id
):
    if not nets:
        return no_update
    if include_unmatched:
        role = ["'non-host'", "'unmatched-non-host'"]
    else:
        role = "non-host"
    filter_name = graph_id["filter"]
    sv = float(slider_values[0])
    query = generate_path_net_scene_by_sec_query(
        nets[PATHNET_GT],
        nets["meta_data"],
        {sv: distances_dict[str(sv)]},
        interesting_filters=PATHNET_BATCH_BY_SEC_FILTERS[filter_name],
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role=role,
    )

    df, _ = run_query_with_nets_names_processing(query)
    return draw_meta_data_filters(
        df,
        title=f"<b>Non-Host {filter_name} Scene Accuracy<b>",
        yaxis="Acc rate",
        xaxis="",
        interesting_columns=list(PATHNET_BATCH_BY_SEC_FILTERS[filter_name].keys()),
        interesting_filters=list(PATHNET_BATCH_BY_SEC_FILTERS[filter_name].values()),
        score_func=lambda row, score_filter: row[f"score_{score_filter}"],
        hover=True,
        count_items_name="dps",
    )


@callback(
    Output({"id": PATH_NET_MISSES_NEXT, "filter": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    State({"id": PATH_NET_MISSES_NEXT, "filter": MATCH}, "id"),
)
def get_path_net_misses_next(meta_data_filters, pathnet_filters, nets, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    query = generate_path_net_miss_false_query(
        nets[PATHNET_GT],
        nets["meta_data"],
        PATHNET_MISS_FALSE_FILTERS[filter_name],
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role=["'non-host'", "'unmatched-non-host'"],
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_meta_data_filters(
        df,
        title="<b>Miss non-host<b>",
        yaxis="Miss rate",
        xaxis="",
        interesting_columns=list(PATHNET_MISS_FALSE_FILTERS[filter_name].keys()),
        interesting_filters=list(PATHNET_MISS_FALSE_FILTERS[filter_name].values()),
        score_func=lambda row, score_filter: row[f"score_{score_filter}"],
        hover=True,
        count_items_name="dps",
    )


@callback(
    Output({"out": "graph", "role": MATCH}, "children"),
    Input(NETS, "data"),
    State({"out": "graph", "role": MATCH}, "id"),
)
def generate_conf_matrices_components(nets, graph_id):
    if not nets:
        return []
    children = generate_matrices_layout(
        nets=nets,
        upper_diag_id={"type": PATH_NET_ALL_TPR, "role": graph_id["role"]},
        lower_diag_id={"type": PATH_NET_HOST_TPR, "role": graph_id["role"]},
        left_conf_mat_id={"type": PATH_NET_ALL_CONF_MATS, "role": graph_id["role"]},
        right_conf_mat_id={"type": PATH_NET_HOST_CONF_MAT, "role": graph_id["role"]},
    )
    return children


def get_column_histogram(meta_data_filters, pathnet_filters, nets, role, column, min_val, max_val, bins_factor):
    if not nets:
        return no_update

    query = generate_count_query(
        nets[PATHNET_GT],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        group_by_column=column,
        role=[f"'{role}'"],
        bins_factor=bins_factor,
        group_by_net_id=True,
        extra_columns=["bias", "view_range"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data[column] = data[column].clip(min_val, max_val)
    data = data.sort_values(by=column)

    units = "(m)" if column == "bias" else "(s)"
    title = f"<b>Distribution of {role} {column} {units}<b>"

    fig = px.line(data, x=column, y="overall", color="net_id", title=title, markers=True)
    fig.update_layout(showlegend=False)
    return fig


@callback(
    Output(PATH_NET_BIASES_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
)
def get_path_net_biases_host(meta_data_filters, pathnet_filters, nets):
    return get_column_histogram(
        meta_data_filters, pathnet_filters, nets, role="host", column="bias", min_val=-2, max_val=2, bins_factor=0.05
    )


@callback(
    Output(PATH_NET_BIASES_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
)
def get_path_net_biases_next(meta_data_filters, pathnet_filters, nets):
    return get_column_histogram(
        meta_data_filters,
        pathnet_filters,
        nets,
        role="non-host",
        column="bias",
        min_val=-2,
        max_val=2,
        bins_factor=0.05,
    )


@callback(
    Output(PATH_NET_VIEW_RANGES_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
)
def get_path_net_view_ranges_host(meta_data_filters, pathnet_filters, nets):
    return get_column_histogram(
        meta_data_filters,
        pathnet_filters,
        nets,
        role="host",
        column="view_range",
        min_val=0,
        max_val=10,
        bins_factor=0.1,
    )


@callback(
    Output(PATH_NET_VIEW_RANGES_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
)
def get_path_net_view_ranges_next(meta_data_filters, pathnet_filters, nets):
    return get_column_histogram(
        meta_data_filters,
        pathnet_filters,
        nets,
        role="non-host",
        column="view_range",
        min_val=0,
        max_val=10,
        bins_factor=0.1,
    )


def in_lane_hover_txt(row, col):
    count = row[f"count_{col}"]
    score = row[f"score_{col}"]
    comp_count = round(count / score) - count
    return f"in-lane dps: {count}<br>out-of-lane dps: {comp_count}"


@callback(
    Output({"id": PATH_NET_OOL, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input(PATHNET_DYNAMIC_THRESHOLD_OOL, "data"),
    Input(PATHNET_DYNAMIC_THRESHOLD_RE_OOL, "data"),
    State({"id": PATH_NET_OOL, "role": MATCH}, "id"),
)
def get_path_net_in_lane_fig(
    meta_data_filters, pathnet_filters, nets, threshold_boundary_dict, threshold_re_dict, graph_id
):
    if not nets:
        return no_update
    boundaries_dist_col_name = "dp_dist_from_boundaries_gt"
    re_dist_col_name = "dp_dist_from_road_edges_gt"

    boundaries_dist_columns = [f'"{boundaries_dist_col_name}_{sec}"' for sec in distances]
    boundaries_dist_columns += [f'"{re_dist_col_name}_{sec}"' for sec in distances]
    role = graph_id["role"]

    query = get_in_lane_query(
        data_tables=nets[PATHNET_BOUNDARIES],
        meta_data=nets["meta_data"],
        boundary_dist_column_name=boundaries_dist_col_name,
        boundary_dist_threshold_dict=threshold_boundary_dict,
        re_dist_column_name=re_dist_col_name,
        re_dist_threshold_dict=threshold_re_dict,
        meta_data_filters=meta_data_filters,
        operator=">",
        role=role,
        base_extra_filters=pathnet_filters,
        extra_columns=boundaries_dist_columns,
    )

    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(
        df, distances, "in-lane accuracy", role=role, yaxis="% accurate dps", hover=True, hover_func=in_lane_hover_txt
    )
