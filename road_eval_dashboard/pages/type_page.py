import dash_bootstrap_components as dbc
from dash import html, dcc, register_page, Input, Output, callback, State, no_update, ALL

from road_eval_dashboard.assets.data_enums import LMType
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
    TYPE_OVERALL,
    TYPE_HOST,
    MD_FILTERS,
    NETS,
    OVERALL_TYPE_CONF_DIAGONAL,
    HOST_TYPE_CONF_DIAGONAL,
    OVERALL_TYPE_CONF_MAT,
    HOST_TYPE_CONF_MAT,
    ALL_TYPE_CONF_MATS,
)
from road_eval_dashboard.components.queries_manager import (
    generate_compare_query,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.graphs.bar_graph import basic_bar_graph


type_class_names = [enum.name for enum in LMType if enum.value != -1]
extra_properties = PageProperties("line-chart")
register_page(__name__, path="/type", name="Type", order=5, **extra_properties.__dict__)

layout = html.Div(
    [
        html.H1("Lane Mark Type", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.gt_layout,
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [loading_wrapper([dcc.Graph(id=TYPE_OVERALL, config={"displayModeBar": False})])], width=6
                        ),
                        dbc.Col(
                            [loading_wrapper([dcc.Graph(id=TYPE_HOST, config={"displayModeBar": False})])], width=6
                        ),
                    ]
                )
            ]
        ),
        html.Div(
            id=ALL_TYPE_CONF_MATS,
        ),
    ]
)


@callback(
    Output(ALL_TYPE_CONF_MATS, "children"),
    Input(NETS, "data"),
)
def generate_matrices_components(nets):
    if not nets:
        return []

    children = generate_matrices_layout(
        nets=nets,
        upper_diag_id=OVERALL_TYPE_CONF_DIAGONAL,
        lower_diag_id=HOST_TYPE_CONF_DIAGONAL,
        left_conf_mat_id=OVERALL_TYPE_CONF_MAT,
        right_conf_mat_id=HOST_TYPE_CONF_MAT,
    )
    return children


@callback(
    Output(OVERALL_TYPE_CONF_DIAGONAL, "figure"),
    Output({"type": OVERALL_TYPE_CONF_MAT, "index": ALL}, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
)
def generate_overall_matrices(meta_data_filters, nets):
    if not nets:
        return no_update

    diagonal_compare, mats_figs = generate_matrices_graphs(
        label_col="type_label",
        pred_col="type_pred",
        nets_tables=nets["pred_tables"],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=type_class_names,
        ca_oriented=True,
    )
    return diagonal_compare, mats_figs


@callback(
    Output(HOST_TYPE_CONF_DIAGONAL, "figure"),
    Output({"type": HOST_TYPE_CONF_MAT, "index": ALL}, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
)
def generate_host_matrices(meta_data_filters, nets):
    if not nets:
        return no_update

    diagonal_compare, mats_figs = generate_matrices_graphs(
        label_col="type_label",
        pred_col="type_pred",
        nets_tables=nets["pred_tables"],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        role="host",
        class_names=type_class_names,
        ca_oriented=True,
    )
    return diagonal_compare, mats_figs


@callback(
    Output(TYPE_OVERALL, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_overall_type_score(meta_data_filters, nets):
    if not nets:
        return no_update

    labels = "type_label"
    preds = "type_pred"
    query = generate_compare_query(
        nets["pred_tables"],
        nets["meta_data"],
        labels,
        preds,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{labels} != -1",
        ca_oriented=True,
    )
    data, _ = run_query_with_nets_names_processing(query)
    fig = basic_bar_graph(data, x="net_id", y="score", title="Overall Type Score", color="net_id")
    return fig


@callback(
    Output(TYPE_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_host_type_score(meta_data_filters, nets):
    if not nets:
        return no_update

    labels = "type_label"
    preds = "type_pred"
    query = generate_compare_query(
        nets["pred_tables"],
        nets["meta_data"],
        labels,
        preds,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{labels} != -1",
        role="host",
        ca_oriented=True,
    )
    data, _ = run_query_with_nets_names_processing(query)
    fig = basic_bar_graph(data, x="net_id", y="score", title="Host Type Score", color="net_id")
    return fig
