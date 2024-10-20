import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, callback, html, no_update, register_page

from road_dashboards.road_eval_dashboard.assets.data_enums import LMCaRel
from road_dashboards.road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_dashboards.road_eval_dashboard.components.components_ids import (
    ALL_CA_REL_CONF_MATS,
    CA_REL_HOST,
    CA_REL_OVERALL,
    CA_REL_OVERALL_DAY,
    CA_REL_OVERALL_NIGHT,
    HOST_CA_REL_CONF_DIAGONAL,
    HOST_CA_REL_CONF_MAT,
    MD_FILTERS,
    NETS,
    OVERALL_CA_REL_CONF_DIAGONAL,
    OVERALL_CA_REL_CONF_MAT,
)
from road_dashboards.road_eval_dashboard.components.confusion_matrices_layout import (
    generate_matrices_graphs,
    generate_matrices_layout,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.page_properties import PageProperties
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_compare_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.bar_graph import basic_bar_graph

ca_rel_class_names = [enum.name for enum in LMCaRel if enum.value != 0]
extra_properties = PageProperties("line-chart")
register_page(__name__, path="/ca_rel", name="CA Rel", order=4, **extra_properties.__dict__)

DAY_FILTER_STR = "mdbi_time_of_day IN ('Day_Sunny', 'Day_Cloudy', 'Day')"
NIGHT_FILTER_STR = "mdbi_time_of_day = 'Night'"


layout = html.Div(
    [
        html.H1("Lane Mark CA Relevant", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.gt_layout,
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col([graph_wrapper(CA_REL_OVERALL)], width=6),
                        dbc.Col([graph_wrapper(CA_REL_HOST)], width=6),
                    ],
                )
            ]
        ),
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [graph_wrapper(CA_REL_OVERALL_DAY)],
                            width=6,
                        ),
                        dbc.Col(
                            [graph_wrapper(CA_REL_OVERALL_NIGHT)],
                            width=6,
                        ),
                    ],
                ),
            ]
        ),
        html.Div(
            id=ALL_CA_REL_CONF_MATS,
        ),
    ]
)


@callback(
    Output(ALL_CA_REL_CONF_MATS, "children"),
    Input(NETS, "data"),
)
def generate_matrices_components(nets):
    if not nets:
        return []

    children = generate_matrices_layout(
        nets=nets,
        upper_diag_id=OVERALL_CA_REL_CONF_DIAGONAL,
        lower_diag_id=HOST_CA_REL_CONF_DIAGONAL,
        left_conf_mat_id=OVERALL_CA_REL_CONF_MAT,
        right_conf_mat_id=HOST_CA_REL_CONF_MAT,
    )
    return children


@callback(
    Output(OVERALL_CA_REL_CONF_DIAGONAL, "figure"),
    Output({"type": OVERALL_CA_REL_CONF_MAT, "index": ALL}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def generate_overall_matrices(meta_data_filters, nets):
    if not nets:
        return no_update

    diagonal_compare, mats_figs = generate_matrices_graphs(
        label_col="ca_relevant_lm_label",
        pred_col="ca_relevant_lm_pred",
        nets_tables=nets["pred_tables"],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=ca_rel_class_names,
        ca_oriented=True,
        ignore_val=0,
    )
    return diagonal_compare, mats_figs


@callback(
    Output(HOST_CA_REL_CONF_DIAGONAL, "figure"),
    Output({"type": HOST_CA_REL_CONF_MAT, "index": ALL}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def generate_host_matrices(meta_data_filters, nets):
    if not nets:
        return no_update

    diagonal_compare, mats_figs = generate_matrices_graphs(
        label_col="ca_relevant_lm_label",
        pred_col="ca_relevant_lm_pred",
        nets_tables=nets["pred_tables"],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        role="host",
        class_names=ca_rel_class_names,
        ca_oriented=True,
        ignore_val=0,
    )
    return diagonal_compare, mats_figs


def get_ca_rel_score(meta_data_filters, nets, role=""):
    labels = "ca_relevant_lm_label"
    preds = "ca_relevant_lm_pred"
    query = generate_compare_query(
        nets["pred_tables"],
        nets["meta_data"],
        labels,
        preds,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{labels} != 0",
        role=role,
        ca_oriented=True,
    )
    data, _ = run_query_with_nets_names_processing(query)
    return data


@callback(
    Output(CA_REL_OVERALL, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_overall_ca_rel_score(meta_data_filters, nets):
    if not nets:
        return no_update

    data = get_ca_rel_score(meta_data_filters, nets)
    fig = basic_bar_graph(data, x="net_id", y="score", title="Overall CA Rel Score", color="net_id")
    return fig


@callback(
    Output(CA_REL_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_host_ca_rel_score(meta_data_filters, nets):
    if not nets:
        return no_update

    data = get_ca_rel_score(meta_data_filters, nets, role="host")
    fig = basic_bar_graph(data, x="net_id", y="score", title="Host CA Rel Score", color="net_id")
    return fig


@callback(
    Output(CA_REL_OVERALL_DAY, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_overall_day_ca_rel_score(meta_data_filters, nets):
    if not nets:
        return no_update

    meta_data_filters = f"({meta_data_filters}) AND ({DAY_FILTER_STR})" if meta_data_filters else DAY_FILTER_STR
    data = get_ca_rel_score(meta_data_filters, nets)
    fig = basic_bar_graph(data, x="net_id", y="score", title="Overall Day CA Rel Score", color="net_id")
    return fig


@callback(
    Output(CA_REL_OVERALL_NIGHT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_overall_night_ca_rel_score(meta_data_filters, nets):
    if not nets:
        return no_update

    meta_data_filters = f"({meta_data_filters}) AND ({NIGHT_FILTER_STR})" if meta_data_filters else NIGHT_FILTER_STR
    data = get_ca_rel_score(meta_data_filters, nets)
    fig = basic_bar_graph(data, x="net_id", y="score", title="Overall Night CA Rel Score", color="net_id")
    return fig
