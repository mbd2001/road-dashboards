from functools import reduce
from operator import iconcat

import dash_bootstrap_components as dbc
import numpy as np
from dash import ALL, MATCH, Input, Output, State, callback, dcc, html, no_update, register_page

from road_eval_dashboard.road_eval_dashboard.components import meta_data_filter
from road_eval_dashboard.road_eval_dashboard.components.components_ids import (
    ALL_SCENE_CONF_DIAGONALS,
    ALL_SCENE_CONF_DIAGONALS_MEST,
    ALL_SCENE_CONF_MATS,
    ALL_SCENE_CONF_MATS_MEST,
    ALL_SCENE_ROC_CURVES,
    ALL_SCENE_SCORES,
    MD_FILTERS,
    NETS,
    SCENE_CONF_DIAGONALS,
    SCENE_CONF_DIAGONALS_MEST,
    SCENE_CONF_MAT,
    SCENE_CONF_MAT_MEST,
    SCENE_ROC_CURVE,
    SCENE_SCORE,
    SCENE_SIGNALS_CONF_MATS_DATA,
    SCENE_SIGNALS_DATA_READY,
    SCENE_SIGNALS_LIST,
)
from road_eval_dashboard.road_eval_dashboard.components.confusion_matrices_layout import generate_conf_matrices
from road_eval_dashboard.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_eval_dashboard.road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.road_eval_dashboard.components.queries_manager import (
    ROC_THRESHOLDS,
    generate_compare_query,
    generate_roc_query,
    process_net_names_list,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.road_eval_dashboard.components import base_dataset_statistics
from road_eval_dashboard.road_eval_dashboard.graphs import (
    basic_bar_graph,
    draw_conf_diagonal_compare,
    draw_confusion_matrix,
    draw_roc_curve,
)

scene_class_names = ["False", "True"]
extra_properties = PageProperties("line-chart")
register_page(__name__, path="/scene", name="Scene", order=8, **extra_properties.__dict__)


def _init_dcc_stores():
    return html.Div(
        [
            dcc.Store(id=SCENE_SIGNALS_CONF_MATS_DATA),
        ]
    )


layout = html.Div(
    [
        html.H1("Scene Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        _init_dcc_stores(),
        html.Div(
            id=ALL_SCENE_SCORES,
        ),
        html.Div(
            id=ALL_SCENE_ROC_CURVES,
        ),
        loading_wrapper([html.Div(id=SCENE_SIGNALS_DATA_READY)]),
        html.Div(
            id=ALL_SCENE_CONF_DIAGONALS_MEST,
        ),
        html.Div(
            id=ALL_SCENE_CONF_DIAGONALS,
        ),
        html.Div(
            id=ALL_SCENE_CONF_MATS_MEST,
        ),
        html.Div(
            id=ALL_SCENE_CONF_MATS,
        ),
    ]
)


def _name2title(name):
    return " ".join(
        [
            (word if word.isupper() else word.capitalize())
            for word in name.replace("scene_", "").replace("_", " ").split()
        ]
    )


def _generate_charts_per_net(base_id, scene_signals):
    # arrange charts in 2 columns such that left/right signals appear
    # first on the same row and then the rest of the signals
    children = []
    lr_signals = [
        [signal, signal.replace("left", "right")]
        for signal in sorted(scene_signals)
        if "left" in signal and signal.replace("left", "right") in scene_signals
    ]
    other_signals = sorted(set(scene_signals) - set(reduce(iconcat, lr_signals, [])))
    for signal_pair in lr_signals:
        children.append(
            dbc.Row(
                [
                    dbc.Col(
                        [graph_wrapper({**base_id, **{"signal": signal_pair[0]}})],
                        width=6,
                    ),
                    dbc.Col(
                        [graph_wrapper({**base_id, **{"signal": signal_pair[1]}})],
                        width=6,
                    ),
                ]
            ),
        )
    for ind, _ in enumerate(other_signals[:-1:2]):
        children.append(
            dbc.Row(
                [
                    dbc.Col(
                        [graph_wrapper({**base_id, **{"signal": other_signals[ind]}})],
                        width=6,
                    ),
                    dbc.Col(
                        [graph_wrapper({**base_id, **{"signal": other_signals[ind + 1]}})],
                        width=6,
                    ),
                ]
            ),
        )
    if len(scene_signals) % 2:
        children.append(
            dbc.Row(
                [
                    dbc.Col(
                        [graph_wrapper({**base_id, **{"signal": other_signals[-1]}})],
                        width=6,
                    ),
                    dbc.Col([], width=6),
                ]
            ),
        )
    return children


def _generate_charts(chart_type, nets, scene_signals_list, per_net=False):
    if not nets or not scene_signals_list:
        return []
    if isinstance(scene_signals_list, dict):
        scene_signals_list = scene_signals_list.get("pred", None)
    if not scene_signals_list:
        return []

    children = []
    children.append(dbc.Row(html.H2(_name2title(chart_type), className="mb-5")))
    base_id = {"type": chart_type}
    if not per_net:
        children.extend(_generate_charts_per_net(base_id, scene_signals_list))
    else:
        net_names = process_net_names_list(nets["names"])
        for net_name in net_names:
            base_id["net"] = net_name
            children.append(dbc.Row(html.H3(base_id["net"], className="mb-5")))
            children.extend(_generate_charts_per_net(base_id, scene_signals_list))
    children = card_wrapper(children)
    return children


@callback(Output(ALL_SCENE_SCORES, "children"), Input(NETS, "data"), Input(SCENE_SIGNALS_LIST, "data"))
def generate_score_charts(nets, scene_signals_list):
    return _generate_charts(SCENE_SCORE, nets, scene_signals_list)


def _generate_matrices_per_signal(nets, meta_data_filters, signal):
    label_col = f"scene_signals_{signal.replace('_mest', '')}_label"
    pred_col = f"scene_signals_{signal}_pred"
    net_names = process_net_names_list(nets["names"])
    if signal.endswith("_mest"):
        net_names = [net_names[0]]
    mats = generate_conf_matrices(
        label_col=label_col,
        pred_col=pred_col,
        nets_tables=nets["frame_tables"],
        meta_data_table=nets["meta_data"],
        net_names=net_names,
        meta_data_filters=meta_data_filters,
        class_names=scene_class_names,
        compare_sign=True,
        ignore_val=0,
    )
    return mats


@callback(
    Output(SCENE_SIGNALS_CONF_MATS_DATA, "data"),
    Output(SCENE_SIGNALS_DATA_READY, "children"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    State(SCENE_SIGNALS_LIST, "data"),
)
def _generate_matrices(meta_data_filters, nets, signals):
    if not nets or not signals:
        return no_update
    conf_mats = {}
    for signal in signals.get("pred", []):
        conf_mats[signal] = _generate_matrices_per_signal(nets, meta_data_filters, signal)
    for signal in signals.get("mest", []):
        signal_name = f"{signal}_mest"
        conf_mats[signal_name] = _generate_matrices_per_signal(nets, meta_data_filters, signal_name)
    notification = dbc.Alert("Confusion matrices data is ready.", color="success", dismissable=True, duration=2000)
    return conf_mats, notification


@callback(
    Output({"type": SCENE_SCORE, "signal": MATCH}, "figure"),
    Input({"type": SCENE_SCORE, "signal": MATCH}, "id"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_scene_score(id, meta_data_filters, nets):
    if not nets:
        return no_update

    signal = id["signal"]
    labels = f"scene_signals_{signal}_label"
    preds = f"scene_signals_{signal}_pred"
    query = generate_compare_query(
        nets["frame_tables"],
        nets["meta_data"],
        labels,
        preds,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{labels} != 0",
        compare_sign=True,
    )
    data, _ = run_query_with_nets_names_processing(query)
    fig = basic_bar_graph(data, x="net_id", y="score", title=f"{_name2title(signal)} Score", color="net_id")
    return fig


@callback(
    Output(ALL_SCENE_ROC_CURVES, "children"),
    Input(NETS, "data"),
    Input(SCENE_SIGNALS_LIST, "data"),
)
def generate_roc_curves(nets, scene_signals_list):
    return _generate_charts(SCENE_ROC_CURVE, nets, scene_signals_list)


@callback(
    Output({"type": SCENE_ROC_CURVE, "signal": MATCH}, "figure"),
    Input({"type": SCENE_ROC_CURVE, "signal": MATCH}, "id"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_scene_roc_curve(id, meta_data_filters, nets):
    if not nets:
        return no_update

    signal = id["signal"]
    label_col = f"scene_signals_{signal}_label"
    pred_col = f"scene_signals_{signal}_pred"
    query = generate_roc_query(
        nets["frame_tables"],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        label_col=label_col,
        pred_col=pred_col,
        thresholds=ROC_THRESHOLDS,
    )
    data, _ = run_query_with_nets_names_processing(query)
    data = data.fillna(1)
    return draw_roc_curve(data, _name2title(signal), thresholds=ROC_THRESHOLDS)


@callback(Output(ALL_SCENE_CONF_DIAGONALS, "children"), Input(NETS, "data"), Input(SCENE_SIGNALS_LIST, "data"))
def generate_scene_conf_diagonals(nets, scene_signals_list):
    return _generate_charts(SCENE_CONF_DIAGONALS, nets, scene_signals_list)


@callback(Output(ALL_SCENE_CONF_MATS, "children"), Input(NETS, "data"), Input(SCENE_SIGNALS_LIST, "data"))
def generate_scene_conf_mats(nets, scene_signals_list):
    return _generate_charts(SCENE_CONF_MAT, nets, scene_signals_list, per_net=True)


def _get_mest_scene_signals(scene_signals_list):
    if not scene_signals_list or not isinstance(scene_signals_list, dict):
        return []
    scene_signals = [f"{signal}_mest" for signal in scene_signals_list.get("mest", [])]
    return scene_signals


@callback(Output(ALL_SCENE_CONF_DIAGONALS_MEST, "children"), Input(NETS, "data"), Input(SCENE_SIGNALS_LIST, "data"))
def generate_scene_conf_diagonals_mest(nets, scene_signals_list):
    scene_signals = _get_mest_scene_signals(scene_signals_list)
    return _generate_charts(SCENE_CONF_DIAGONALS_MEST, nets, scene_signals)


@callback(Output(ALL_SCENE_CONF_MATS_MEST, "children"), Input(NETS, "data"), Input(SCENE_SIGNALS_LIST, "data"))
def generate_scene_conf_mats_mest(nets, scene_signals_list):
    scene_signals = _get_mest_scene_signals(scene_signals_list)
    return _generate_charts(SCENE_CONF_MAT_MEST, nets, scene_signals)


def _generate_scene_conf_mat_chart(id, conf_mats):
    if not conf_mats:
        return no_update
    signal = id["signal"]
    try:
        net = id["net"]
    except KeyError:
        net = next(iter(conf_mats[signal].keys()))
    mat_name = _name2title(signal)
    return draw_confusion_matrix(
        np.array(conf_mats[signal][net]["conf_matrix"]),
        np.array(conf_mats[signal][net]["normalize_mat"]),
        scene_class_names,
        mat_name=mat_name,
    )


@callback(
    Output({"type": SCENE_CONF_MAT, "net": ALL, "signal": MATCH}, "figure"),
    Input({"type": SCENE_CONF_MAT, "net": ALL, "signal": MATCH}, "id"),
    Input(SCENE_SIGNALS_CONF_MATS_DATA, "data"),
)
def generate_scene_conf_mat_chart(ids, conf_mats):
    figs = []
    for id in ids:
        figs.append(_generate_scene_conf_mat_chart(id, conf_mats))
    return figs


@callback(
    Output({"type": SCENE_CONF_MAT_MEST, "signal": MATCH}, "figure"),
    Input({"type": SCENE_CONF_MAT_MEST, "signal": MATCH}, "id"),
    Input(SCENE_SIGNALS_CONF_MATS_DATA, "data"),
)
def generate_scene_conf_mat_chart_mest(id, conf_mats):
    return _generate_scene_conf_mat_chart(id, conf_mats)


def _generate_scene_conf_diagonals_chart(id, conf_mats):
    if not conf_mats:
        return no_update
    signal = id["signal"]
    normalize_mats = [np.array(mat["normalize_mat"]) for mat in conf_mats[signal].values()]
    net_names = list(conf_mats[signal].keys())
    mat_name = _name2title(signal)
    return draw_conf_diagonal_compare(normalize_mats, net_names, scene_class_names, mat_name=mat_name)


@callback(
    Output({"type": SCENE_CONF_DIAGONALS, "signal": MATCH}, "figure"),
    Input({"type": SCENE_CONF_DIAGONALS, "signal": MATCH}, "id"),
    Input(SCENE_SIGNALS_CONF_MATS_DATA, "data"),
)
def generate_scene_conf_diagonal_chart(id, conf_mats):
    return _generate_scene_conf_diagonals_chart(id, conf_mats)


@callback(
    Output({"type": SCENE_CONF_DIAGONALS_MEST, "signal": MATCH}, "figure"),
    Input({"type": SCENE_CONF_DIAGONALS_MEST, "signal": MATCH}, "id"),
    Input(SCENE_SIGNALS_CONF_MATS_DATA, "data"),
)
def generate_scene_conf_diagonals_mest_chart(id, conf_mats):
    return _generate_scene_conf_diagonals_chart(id, conf_mats)
