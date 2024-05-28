import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, callback, html, no_update, register_page

from road_eval_dashboard.road_eval_dashboard.assets.data_enums import LMColor
from road_eval_dashboard.road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_eval_dashboard.road_eval_dashboard.components.components_ids import (
    ALL_COLOR_CONF_MATS,
    COLOR_HOST,
    COLOR_OVERALL,
    COLOR_OVERALL_DAY,
    COLOR_OVERALL_NIGHT,
    HOST_COLOR_CONF_DIAGONAL,
    HOST_COLOR_CONF_MAT,
    MD_FILTERS,
    NETS,
    OVERALL_COLOR_CONF_DIAGONAL,
    OVERALL_COLOR_CONF_MAT,
)
from road_eval_dashboard.road_eval_dashboard.components.confusion_matrices_layout import (
    generate_matrices_graphs,
    generate_matrices_layout,
)
from road_eval_dashboard.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_eval_dashboard.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_eval_dashboard.road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.road_eval_dashboard.components.queries_manager import (
    generate_compare_query,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.road_eval_dashboard.graphs.bar_graph import basic_bar_graph

color_class_names = [enum.name for enum in LMColor]
extra_properties = PageProperties("line-chart")
register_page(__name__, path="/color", name="Color", order=4, **extra_properties.__dict__)

DAY_FILTER_STR = "mdbi_time_of_day IN ('Day_Sunny', 'Day_Cloudy', 'Day')"
NIGHT_FILTER_STR = "mdbi_time_of_day = 'Night'"


layout = html.Div(
    [
        html.H1("Lane Mark Color", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.gt_layout,
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col([graph_wrapper(COLOR_OVERALL)], width=6),
                        dbc.Col([graph_wrapper(COLOR_HOST)], width=6),
                    ],
                )
            ]
        ),
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [graph_wrapper(COLOR_OVERALL_DAY)],
                            width=6,
                        ),
                        dbc.Col(
                            [graph_wrapper(COLOR_OVERALL_NIGHT)],
                            width=6,
                        ),
                    ],
                ),
            ]
        ),
        html.Div(
            id=ALL_COLOR_CONF_MATS,
        ),
    ]
)


@callback(
    Output(ALL_COLOR_CONF_MATS, "children"),
    Input(NETS, "data"),
)
def generate_matrices_components(nets):
    if not nets:
        return []

    children = generate_matrices_layout(
        nets=nets,
        upper_diag_id=OVERALL_COLOR_CONF_DIAGONAL,
        lower_diag_id=HOST_COLOR_CONF_DIAGONAL,
        left_conf_mat_id=OVERALL_COLOR_CONF_MAT,
        right_conf_mat_id=HOST_COLOR_CONF_MAT,
    )
    return children


@callback(
    Output(OVERALL_COLOR_CONF_DIAGONAL, "figure"),
    Output({"type": OVERALL_COLOR_CONF_MAT, "index": ALL}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def generate_overall_matrices(meta_data_filters, nets):
    if not nets:
        return no_update

    diagonal_compare, mats_figs = generate_matrices_graphs(
        label_col="color_label",
        pred_col="color_pred",
        nets_tables=nets["pred_tables"],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=color_class_names,
        ca_oriented=True,
    )
    return diagonal_compare, mats_figs


@callback(
    Output(HOST_COLOR_CONF_DIAGONAL, "figure"),
    Output({"type": HOST_COLOR_CONF_MAT, "index": ALL}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def generate_host_matrices(meta_data_filters, nets):
    if not nets:
        return no_update

    diagonal_compare, mats_figs = generate_matrices_graphs(
        label_col="color_label",
        pred_col="color_pred",
        nets_tables=nets["pred_tables"],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        role="host",
        class_names=color_class_names,
        ca_oriented=True,
    )
    return diagonal_compare, mats_figs


def get_color_score(meta_data_filters, nets, role=""):
    labels = "color_label"
    preds = "color_pred"
    query = generate_compare_query(
        nets["pred_tables"],
        nets["meta_data"],
        labels,
        preds,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{labels} != -1",
        role=role,
        ca_oriented=True,
    )
    data, _ = run_query_with_nets_names_processing(query)
    return data


@callback(
    Output(COLOR_OVERALL, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_overall_color_score(meta_data_filters, nets):
    if not nets:
        return no_update

    data = get_color_score(meta_data_filters, nets)
    fig = basic_bar_graph(data, x="net_id", y="score", title="Overall Color Score", color="net_id")
    return fig


@callback(
    Output(COLOR_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_host_color_score(meta_data_filters, nets):
    if not nets:
        return no_update

    data = get_color_score(meta_data_filters, nets, role="host")
    fig = basic_bar_graph(data, x="net_id", y="score", title="Host Color Score", color="net_id")
    return fig


@callback(
    Output(COLOR_OVERALL_DAY, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_overall_day_color_score(meta_data_filters, nets):
    if not nets:
        return no_update

    meta_data_filters = meta_data_filters + f" AND {DAY_FILTER_STR}" if meta_data_filters else DAY_FILTER_STR
    data = get_color_score(meta_data_filters, nets)
    fig = basic_bar_graph(data, x="net_id", y="score", title="Overall Day Color Score", color="net_id")
    return fig


@callback(
    Output(COLOR_OVERALL_NIGHT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_overall_night_color_score(meta_data_filters, nets):
    if not nets:
        return no_update

    meta_data_filters = meta_data_filters + f" AND {NIGHT_FILTER_STR}" if meta_data_filters else NIGHT_FILTER_STR
    data = get_color_score(meta_data_filters, nets)
    fig = basic_bar_graph(data, x="net_id", y="score", title="Overall Night Color Score", color="net_id")
    return fig
