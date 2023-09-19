import dash_bootstrap_components as dbc
from dash import html, dcc, register_page, Input, Output, callback, State, no_update, ALL

from road_eval_dashboard.components.confusion_matrices_layout import (
    generate_matrices_graphs,
    generate_matrices_layout,
)
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components import (
    meta_data_filter,
    base_dataset_statistics,
)
from road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS,
    ALL_SCENE_CONF_MATS,
    SCENE_RIGHT,
    SCENE_LEFT,
    RIGHT_SCENE_CONF_MAT,
    LEFT_SCENE_CONF_MAT,
    RIGHT_SCENE_CONF_DIAGONAL,
    LEFT_SCENE_CONF_DIAGONAL,
)
from road_eval_dashboard.components.queries_manager import (
    generate_compare_query,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.graphs.bar_graph import basic_bar_graph


scene_class_names = ["False", "True"]
extra_properties = PageProperties("line-chart")
register_page(__name__, path="/scene", name="Scene", order=8, **extra_properties.__dict__)

layout = html.Div(
    [
        html.H1("Scene Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [loading_wrapper([dcc.Graph(id=SCENE_LEFT, config={"displayModeBar": False})])], width=6
                        ),
                        dbc.Col(
                            [loading_wrapper([dcc.Graph(id=SCENE_RIGHT, config={"displayModeBar": False})])], width=6
                        ),
                    ]
                )
            ]
        ),
        html.Div(
            id=ALL_SCENE_CONF_MATS,
        ),
    ]
)


@callback(
    Output(ALL_SCENE_CONF_MATS, "children"),
    Input(NETS, "data"),
)
def generate_matrices_components(nets):
    if not nets:
        return []

    children = generate_matrices_layout(
        nets=nets,
        upper_diag_id=LEFT_SCENE_CONF_DIAGONAL,
        lower_diag_id=RIGHT_SCENE_CONF_DIAGONAL,
        left_conf_mat_id=LEFT_SCENE_CONF_MAT,
        right_conf_mat_id=RIGHT_SCENE_CONF_MAT,
    )
    return children


@callback(
    Output(LEFT_SCENE_CONF_DIAGONAL, "figure"),
    Output({"type": LEFT_SCENE_CONF_MAT, "index": ALL}, "figure"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
)
def generate_left_matrices(nets, meta_data_filters):
    if not nets:
        return no_update

    label_col = "availability_shadowsguardrail_hostleft_label"
    pred_col = "availability_shadowsguardrail_hostleft_pred"
    diagonal_compare, mats_figs = generate_matrices_graphs(
        label_col=label_col,
        pred_col=pred_col,
        nets_tables=nets["frame_tables"],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        include_all=True,
        class_names=scene_class_names,
        compare_sign=True,
        ignore_val=0,
        conf_name="shadowsguardrail hostleft",
    )
    return diagonal_compare, mats_figs


@callback(
    Output(RIGHT_SCENE_CONF_DIAGONAL, "figure"),
    Output({"type": RIGHT_SCENE_CONF_MAT, "index": ALL}, "figure"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
)
def generate_right_matrices(nets, meta_data_filters):
    if not nets:
        return no_update

    label_col = "availability_shadowsguardrail_hostright_label"
    pred_col = "availability_shadowsguardrail_hostright_pred"
    diagonal_compare, mats_figs = generate_matrices_graphs(
        label_col=label_col,
        pred_col=pred_col,
        nets_tables=nets["frame_tables"],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        include_all=True,
        class_names=scene_class_names,
        compare_sign=True,
        ignore_val=0,
        conf_name="shadowsguardrail hostright",
    )
    return diagonal_compare, mats_figs


@callback(
    Output(SCENE_LEFT, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_left_scene_score(meta_data_filters, nets):
    if not nets:
        return no_update

    labels = "availability_shadowsguardrail_hostleft_label"
    preds = "availability_shadowsguardrail_hostleft_pred"
    query = generate_compare_query(
        nets["frame_tables"],
        nets["meta_data"],
        labels,
        preds,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{labels} != 0",
        include_all=True,
        compare_sign=True,
    )
    data, _ = run_query_with_nets_names_processing(query)
    fig = basic_bar_graph(data, x="net_id", y="score", title="Shadowsguardrail Hostleft Score", color="net_id")
    return fig


@callback(
    Output(SCENE_RIGHT, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_right_scene_score(meta_data_filters, nets):
    if not nets:
        return no_update

    labels = "availability_shadowsguardrail_hostright_label"
    preds = "availability_shadowsguardrail_hostright_pred"
    query = generate_compare_query(
        nets["frame_tables"],
        nets["meta_data"],
        labels,
        preds,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{labels} != 0",
        include_all=True,
        compare_sign=True,
    )
    data, _ = run_query_with_nets_names_processing(query)
    fig = basic_bar_graph(data, x="net_id", y="score", title="Shadowsguardrail Hostright Score", color="net_id")
    return fig
