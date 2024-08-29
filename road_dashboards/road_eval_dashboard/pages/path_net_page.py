import dash_bootstrap_components as dbc
import plotly.express as px
from dash import ALL, MATCH, Input, Output, State, callback, dcc, html, no_update, register_page
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_dashboards.road_eval_dashboard.components.common_filters import (
    PATHNET_MISS_FALSE_FILTERS,
    PATHNET_ROAD_FILTERS,
)
from road_dashboards.road_eval_dashboard.components.components_ids import (
    BIN_POPULATION_DROPDOWN,
    MD_FILTERS,
    NETS,
    PATH_NET_ACC_HOST,
    PATH_NET_ACC_NEXT,
    PATH_NET_ALL_CONF_MATS,
    PATH_NET_ALL_TPR,
    PATH_NET_BIASES_HOST,
    PATH_NET_BIASES_NEXT,
    PATH_NET_FALSES_HOST,
    PATH_NET_FALSES_NEXT,
    PATH_NET_HOST_CONF_MAT,
    PATH_NET_HOST_TPR,
    PATH_NET_MISSES_HOST,
    PATH_NET_MISSES_NEXT,
    PATH_NET_MONOTONE_ACC_HOST,
    PATH_NET_MONOTONE_ACC_NEXT,
    PATH_NET_QUALITY_FALSE_HOST_CORRECT_REJECTION,
    PATH_NET_QUALITY_FALSE_NEXT_CORRECT_REJECTION,
    PATH_NET_QUALITY_HOST_FN,
    PATH_NET_QUALITY_HOST_FP,
    PATH_NET_QUALITY_HOST_TN,
    PATH_NET_QUALITY_NEXT_FN,
    PATH_NET_QUALITY_NEXT_FP,
    PATH_NET_QUALITY_NEXT_TN,
    PATH_NET_QUALITY_TP,
    PATH_NET_VIEW_RANGES_HOST,
    PATH_NET_VIEW_RANGES_NEXT,
    PATHNET_FILTERS,
    PATHNET_GT,
    PATHNET_PRED,
    ROLE_POPULATION_VALUE,
    SPLIT_ROLE_POPULATION_DROPDOWN,
)
from road_dashboards.road_eval_dashboard.components.confusion_matrices_layout import (
    generate_matrices_graphs,
    generate_matrices_layout,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_dashboards.road_eval_dashboard.components.page_properties import PageProperties
from road_dashboards.road_eval_dashboard.components.pathnet_events_extractor.layout import (
    layout as events_extractor_card,
)
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    PATHNET_ACC_THRESHOLDS,
    distances,
    generate_avail_query,
    generate_count_query,
    generate_path_net_dp_quality_query,
    generate_path_net_dp_quality_true_rejection_query,
    generate_path_net_miss_false_query,
    generate_path_net_query,
    generate_pathnet_cumulative_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters
from road_dashboards.road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph
from road_dashboards.road_eval_dashboard.utils.colors import GREEN, RED
from road_dashboards.road_eval_dashboard.utils.url_state_utils import create_dropdown_options_list

basic_operations = create_dropdown_options_list(
    labels=["Greater", "Greater or equal", "Less", "Less or equal", "Equal", "Not Equal", "Is NULL", "Is not NULL"],
    values=[">", ">=", "<", "<=", "=", "<>", "IS NULL", "IS NOT NULL"],
)


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
                                id={"id": f"acc threshold", "ind": i},
                                style={"text-align": "center", "fontSize": "20px"},
                            ),
                            dcc.RangeSlider(
                                id={"id": f"dist-column-slider", "ind": i},
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


extra_properties = PageProperties("line-chart")
register_page(__name__, path="/path_net", name="Path Net", order=9, **extra_properties.__dict__)

role_layout = html.Div([html.Div(id={"out": "graph", "role": role}) for role in ["split", "merge", "primary"]])
pos_layout = html.Div(
    [
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            graph_wrapper(PATH_NET_ACC_HOST),
                            width=6,
                        ),
                        dbc.Col(
                            graph_wrapper(PATH_NET_ACC_NEXT),
                            width=6,
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
            ]
        )
    ]
    + get_cumulative_acc_layout()
    + get_miss_false_layout()
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

quality_layout = html.Div(
    [
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(graph_wrapper(PATH_NET_QUALITY_FALSE_HOST_CORRECT_REJECTION), width=6),
                        dbc.Col(graph_wrapper(PATH_NET_QUALITY_FALSE_NEXT_CORRECT_REJECTION), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_TP, "role": "host"}), width=6),
                        dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_TP, "role": "non-host"}), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(graph_wrapper(PATH_NET_QUALITY_HOST_TN), width=6),
                        dbc.Col(graph_wrapper(PATH_NET_QUALITY_NEXT_TN), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(graph_wrapper(PATH_NET_QUALITY_HOST_FP), width=6),
                        dbc.Col(graph_wrapper(PATH_NET_QUALITY_NEXT_FP), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(graph_wrapper(PATH_NET_QUALITY_HOST_FN), width=6),
                        dbc.Col(graph_wrapper(PATH_NET_QUALITY_NEXT_FN), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        html.Label("quality-threshold (score)", style={"text-align": "center", "fontSize": "20px"}),
                        dcc.RangeSlider(
                            id="quality-threshold-slider", min=-3, max=3, step=0.1, value=[0], allowCross=False
                        ),
                    ]
                ),
            ]
        )
    ]
)

TABS_LAYOUTS = {"positional": pos_layout, "roles": role_layout, "pathnet-quality-score": quality_layout}

layout = html.Div(
    [
        html.H1("Path Net Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.dp_layout,
        events_extractor_card,
        card_wrapper(
            [
                dcc.Tabs(
                    id="pathnet-metrics-graphs",
                    value="positional",
                    children=[
                        dcc.Tab(label="pathnet-metrics-positional", value="positional"),
                        dcc.Tab(label="pathnet-metrics-roles", value="roles"),
                        dcc.Tab(label="DPs Quality", value="pathnet-quality-score"),
                    ],
                ),
            ]
        ),
        card_wrapper(
            [
                dbc.Row([dbc.Col(loading_wrapper(dcc.Dropdown(id=BIN_POPULATION_DROPDOWN, value="")), width=4)]),
                dbc.Row(
                    [
                        dbc.Col(loading_wrapper(dcc.Dropdown(id=SPLIT_ROLE_POPULATION_DROPDOWN, value="")), width=4),
                        dbc.Col(
                            loading_wrapper(dcc.Dropdown(id="roles_operation", options=basic_operations, value="")),
                            width=4,
                        ),
                        dbc.Col(loading_wrapper(dcc.Dropdown(id=ROLE_POPULATION_VALUE, value="")), width=4),
                    ]
                ),
                dbc.Row([dbc.Col(dbc.Button("Update Filters", id="pathnet_update_filters_btn", color="success"))]),
            ]
        ),
        html.Div(id="pathnet-metrics-content"),
    ]
)
ROLE_CLASSES_NAMES = {
    "split": ["NONE", "SPLIT_LEFT", "SPLIT_RIGHT", "IGNORE"],
    "merge": ["NONE", "MERGE_LEFT", "MERGE_RIGHT", "IGNORE"],
    "primary": ["NONE", "PRIMARY", "SECONDARY", "IGNORE", "UNDEFINED"],
}


@callback(Output("pathnet-metrics-content", "children"), Input("pathnet-metrics-graphs", "value"))
def render_content(tab):
    return TABS_LAYOUTS[tab]


@callback(
    Output(PATHNET_FILTERS, "data"),
    State(BIN_POPULATION_DROPDOWN, "value"),
    State(SPLIT_ROLE_POPULATION_DROPDOWN, "value"),
    State(ROLE_POPULATION_VALUE, "value"),
    State("roles_operation", "value"),
    Input("pathnet_update_filters_btn", "n_clicks"),
)
def update_pathnet_filters(bin_population, column, value, roles_operation, n_clicks):
    if (not bin_population and not column and not value) or not n_clicks:
        return ""
    filters = []
    if bin_population:
        filters.append(f"bin_population = '{bin_population}'")
    if column and roles_operation and value is not None:
        filters.append(f"{column} {roles_operation} {value}")

    return " AND ".join(filters)


@callback(
    Output(BIN_POPULATION_DROPDOWN, "options"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def create_population_dropdown(meta_data_filters, nets):
    if not nets:
        return no_update
    query = generate_avail_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters,
        column_name="bin_population",
    )
    df, _ = run_query_with_nets_names_processing(query)
    return create_dropdown_options_list(labels=df["bin_population"])


@callback(
    Output(SPLIT_ROLE_POPULATION_DROPDOWN, "options"),
    Input(NETS, "data"),
)
def create_dp_split_role_dropdown(nets):
    if not nets:
        return no_update
    return create_dropdown_options_list(labels=["split_role", "matched_split_role", "ignore_role"])


@callback(
    Output(ROLE_POPULATION_VALUE, "options"),
    Input(SPLIT_ROLE_POPULATION_DROPDOWN, "value"),
    State(MD_FILTERS, "data"),
    State(NETS, "data"),
)
def create_dp_split_role_dropdown(split_role_population_values, meta_data_filters, nets):
    if not split_role_population_values or not nets:
        return no_update
    query = generate_avail_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters,
        column_name=split_role_population_values,
        extra_columns=[split_role_population_values],
    )
    df, _ = run_query_with_nets_names_processing(query)
    values = set(df[split_role_population_values])
    return create_dropdown_options_list(labels=values)


@callback(
    Output(PATH_NET_ACC_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input("acc-threshold-slider", "value"),
)
def get_path_net_acc_host(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update
    query = generate_path_net_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        "accuracy",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role="host",
        base_dists=slider_values,
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy", role="host", yaxis="% accurate dps")


@callback(
    Output({"id": PATH_NET_MONOTONE_ACC_HOST, "ind": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input({"id": f"dist-column-slider", "ind": MATCH}, "value"),
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
    Input({"id": f"dist-column-slider", "ind": MATCH}, "value"),
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
    Input("acc-threshold-slider", "value"),
)
def get_path_net_acc_next(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update
    query = generate_path_net_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        "accuracy",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role="non-host",
        base_dists=slider_values,
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
        title=f"<b>Miss Host<b>",
        yaxis="Miss rate",
        xaxis="",
        interesting_columns=list(PATHNET_MISS_FALSE_FILTERS[filter_name].keys()),
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
        title=f"<b>Miss non-host<b>",
        yaxis="Miss rate",
        xaxis="",
        interesting_columns=list(PATHNET_MISS_FALSE_FILTERS[filter_name].keys()),
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


@callback(
    Output({"type": PATH_NET_ALL_TPR, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_ALL_CONF_MATS, "role": MATCH, "index": ALL}, "figure"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
    State({"type": PATH_NET_ALL_TPR, "role": MATCH}, "id"),
    Input(PATHNET_FILTERS, "data"),
)
def generate_overall_conf_matrices(nets, meta_data_filters, graph_id, pathnet_filters):
    if not nets:
        return no_update
    role = graph_id["role"]
    diagonal_compare, mats_figs = generate_matrices_graphs(
        pred_col=f"{role}_role",
        label_col=f"matched_{role}_role",
        nets_tables=nets[PATHNET_PRED],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=ROLE_CLASSES_NAMES[role],
        mat_name=f"{role} TPR for all dps",
        extra_filters=pathnet_filters,
    )
    return diagonal_compare, mats_figs


@callback(
    Output({"type": PATH_NET_HOST_TPR, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_HOST_CONF_MAT, "index": ALL, "role": MATCH}, "figure"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
    State({"type": PATH_NET_ALL_TPR, "role": MATCH}, "id"),
    Input(PATHNET_FILTERS, "data"),
)
def generate_host_conf_matrices(nets, meta_data_filters, graph_id, pathnet_filters):
    if not nets:
        return no_update
    if pathnet_filters:
        pathnet_filters = f"{pathnet_filters} AND role = 'host'"
    else:
        pathnet_filters = "role = 'host'"
    role = graph_id["role"]
    diagonal_compare, mats_figs = generate_matrices_graphs(
        pred_col=f"{role}_role",
        label_col=f"matched_{role}_role",
        nets_tables=nets[PATHNET_PRED],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=ROLE_CLASSES_NAMES[role],
        mat_name=f"{role} TPR for host dp",
        extra_filters=pathnet_filters,
    )

    return diagonal_compare, mats_figs


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


@callback(
    Output({"type": PATH_NET_QUALITY_TP, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
    State({"type": PATH_NET_QUALITY_TP, "role": MATCH}, "id"),
)
def get_path_net_quality_score_tp(meta_data_filters, nets, slider_values, idx):
    if not nets:
        return no_update

    acc_dist_operator = "<"
    quality_operator = ">"

    role = idx["role"]
    query = generate_path_net_dp_quality_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role=role,
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df, cols=distances, title="DPs Quality Score - TP", role=role, yaxis="% hit", plot_bgcolor=GREEN
    )
    return fig


@callback(
    Output(PATH_NET_QUALITY_HOST_TN, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
)
def get_path_net_quality_score_host_tn(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update
    acc_dist_operator = ">"
    quality_operator = "<="

    query = generate_path_net_dp_quality_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        extra_filters="",
        role="host",
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df,
        cols=distances,
        title="DPs Quality Score - TN",
        role="host",
        yaxis="% correct rejection",
        plot_bgcolor=GREEN,
    )
    return fig


@callback(
    Output(PATH_NET_QUALITY_NEXT_TN, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
)
def get_path_net_quality_score_next_tn(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update
    acc_dist_operator = ">"
    quality_operator = "<="

    query = generate_path_net_dp_quality_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        extra_filters="",
        role="non-host",
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df,
        cols=distances,
        title="DPs Quality Score - TN",
        role="non-host",
        yaxis="% correct rejection",
        plot_bgcolor=GREEN,
    )
    return fig


@callback(
    Output(PATH_NET_QUALITY_HOST_FP, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
)
def get_path_net_quality_score_host_fp(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update

    acc_dist_operator = "<"
    quality_operator = "<="

    query = generate_path_net_dp_quality_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role="host",
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df, cols=distances, title="DPs Quality Score - FP", role="host", yaxis="% false alarm", plot_bgcolor=RED
    )
    return fig


@callback(
    Output(PATH_NET_QUALITY_NEXT_FP, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
)
def get_path_net_quality_score_next_fp(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update

    acc_dist_operator = "<"
    quality_operator = "<="

    query = generate_path_net_dp_quality_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        extra_filters="",
        role="non-host",
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df,
        cols=distances,
        title="DPs Quality Score - FP",
        role="non-host",
        yaxis="% false alarm",
        plot_bgcolor=RED,
    )
    return fig


@callback(
    Output(PATH_NET_QUALITY_HOST_FN, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
)
def get_path_net_quality_score_host_fn(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update

    acc_dist_operator = ">"
    quality_operator = ">"

    query = generate_path_net_dp_quality_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role="host",
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df, cols=distances, title="DPs Quality Score - FN", role="host", yaxis="% miss", plot_bgcolor=RED
    )
    return fig


@callback(
    Output(PATH_NET_QUALITY_NEXT_FN, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
)
def get_path_net_quality_score_next_fp(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update

    acc_dist_operator = ">"
    quality_operator = ">"

    query = generate_path_net_dp_quality_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        extra_filters="",
        role="non-host",
        base_dists=[0.2, 0.5],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df, cols=distances, title="DPs Quality Score - FN", role="non-host", yaxis="% miss", plot_bgcolor=RED
    )
    return fig


@callback(
    Output(PATH_NET_QUALITY_FALSE_HOST_CORRECT_REJECTION, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
)
def get_path_net_quality_score_host_unmatched_correct_rejection(
    meta_data_filters, pathnet_filters, nets, slider_values
):
    if not nets:
        return no_update

    acc_dist_operator = ">"
    quality_operator = "<"

    query = generate_path_net_dp_quality_true_rejection_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        extra_filters="",
        role=["'host'", "'unmatched-host'"],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df,
        cols=distances,
        title="DPs Quality - Unmatched Corrcert Rejection",
        role="host",
        yaxis="% correct rejection",
        plot_bgcolor=GREEN,
    )
    return fig


@callback(
    Output(PATH_NET_QUALITY_FALSE_NEXT_CORRECT_REJECTION, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
)
def get_path_net_quality_score_next_unmatched_correct_rejection(
    meta_data_filters, pathnet_filters, nets, slider_values
):
    if not nets:
        return no_update

    acc_dist_operator = ">"
    quality_operator = "<"

    query = generate_path_net_dp_quality_true_rejection_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        extra_filters="",
        role=["'non-host'", "'unmatched-non-host'"],
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=slider_values[0],
    )
    df, _ = run_query_with_nets_names_processing(query)
    fig = draw_path_net_graph(
        data=df,
        cols=distances,
        title="DPs Quality - Unmatched Corrcert Rejection",
        role="non-host",
        yaxis="% correct rejection",
        plot_bgcolor=GREEN,
    )
    return fig
