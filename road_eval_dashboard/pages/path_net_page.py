import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, dcc, html, no_update, register_page, MATCH
from road_database_toolkit.athena.athena_utils import query_athena

from road_eval_dashboard.components import base_dataset_statistics, meta_data_filter, pathnet_data_filter
from road_eval_dashboard.components.components_ids import (
    BIN_POPULATION_DROPDOWN,
    MD_FILTERS,
    NETS,
    PATH_NET_ACC_HOST,
    PATH_NET_ACC_NEXT,
    PATHNET_CONF_MAT_ID_DICT,
    PATH_NET_BIASES_HOST,
    PATH_NET_BIASES_NEXT,
    PATH_NET_FALSES_HOST,
    PATH_NET_FALSES_NEXT,
    PATH_NET_MISSES_HOST,
    PATH_NET_MISSES_NEXT,
    PATH_NET_VIEW_RANGES_HOST,
    PATH_NET_VIEW_RANGES_NEXT,
    PATHNET_FILTERS,
    PATHNET_GT,
    PATHNET_PRED,
    ROLE_POPULATION_VALUE,
    SPLIT_ROLE_POPULATION_DROPDOWN,
    PATH_NET_ALL_TPR,
    PATH_NET_HOST_TPR,
    PATH_NET_HOST_CONF_MAT,
    PATH_NET_ALL_CONF_MATS,
)
from road_eval_dashboard.components.confusion_matrices_layout import generate_matrices_graphs, generate_matrices_layout
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.components.queries_manager import (
    distances,
    generate_avail_query,
    generate_count_query,
    generate_path_net_query,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.graphs.histogram_plot import basic_histogram_plot
from road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph

basic_operations = [
    {"label": "Greater", "value": ">"},
    {"label": "Greater or equal", "value": ">="},
    {"label": "Less", "value": "<"},
    {"label": "Less or equal", "value": "<="},
    {"label": "Equal", "value": "="},
    {"label": "Not Equal", "value": "<>"},
    {"label": "Is NULL", "value": "IS NULL"},
    {"label": "Is not NULL", "value": "IS NOT NULL"},
]
extra_properties = PageProperties("line-chart")
register_page(__name__, path="/path_net", name="Path Net", order=9, **extra_properties.__dict__)

role_layout = html.Div([html.Div(id={"out": "graph", "role": role}) for role in ["split", "merge", "primary"]])
pos_layout = html.Div([
    card_wrapper(
        [
            dbc.Row(
                [
                    dcc.RangeSlider(
                        id='acc-threshold-slider',
                        min=0,
                        max=2,
                        step=0.1,
                        value=[0.2, 0.5]
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=PATH_NET_ACC_HOST, config={"displayModeBar": False})]),
                        width=6,
                    ),
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=PATH_NET_ACC_NEXT, config={"displayModeBar": False})]),
                        width=6,
                    ),
                ]
            )
        ]
    ),
    card_wrapper(
        [
            dbc.Row(
                [
                    dcc.RangeSlider(
                        id='falses-threshold-slider',
                        min=0,
                        max=2,
                        step=0.1,
                        value=[0.5, 1]
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=PATH_NET_FALSES_HOST, config={"displayModeBar": False})]),
                        width=6,
                    ),
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=PATH_NET_FALSES_NEXT, config={"displayModeBar": False})]),
                        width=6,
                    ),
                ]
            )
        ]
    ),
    card_wrapper(
        [
            dbc.Row(
                [
                    dcc.RangeSlider(
                        id='misses-threshold-slider',
                        min=0,
                        max=2,
                        step=0.1,
                        value=[0.5, 1]
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=PATH_NET_MISSES_HOST, config={"displayModeBar": False})]),
                        width=6,
                    ),
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=PATH_NET_MISSES_NEXT, config={"displayModeBar": False})]),
                        width=6,
                    ),
                ]
            )
        ]
    ),
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
    )])
TABS_LAYOUTS = {"positional": pos_layout, "roles": role_layout}

layout = html.Div(
    [
        html.H1("Path Net Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.dp_layout,
        dcc.Tabs(id="pathnet-metrics-graphs", value='pathnet-metrics-positional', children=[
            dcc.Tab(label='pathnet-metrics-positional', value='positional'),
            dcc.Tab(label='pathnet-metrics-roles', value='roles'),
        ]),
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
        html.Div(id='pathnet-metrics-content'),
    ]
)
ROLE_CLASSES_NAMES = {"split": ["NONE", "SPLIT_LEFT", "SPLIT_RIGHT", "IGNORE"],
                      "merge": ["NONE", "MERGE_LEFT", "MERGE_RIGHT", "IGNORE"],
                      "primary": ["NONE", "PRIMARY", "SECONDARY", "IGNORE", "UNDEFINED"]
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
    background=False
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
    background=False,
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
    return [{"label": population, "value": population} for population in df["bin_population"]]


@callback(
    Output(SPLIT_ROLE_POPULATION_DROPDOWN, "options"),
    Input(NETS, "data"),
    background=False,
)
def create_dp_split_role_dropdown(nets):
    if not nets:
        return no_update
    options = [
        {"label": "split_role", "value": "split_role"},
        {"label": "matched_split_role", "value": "matched_split_role"},
    ]
    return options


@callback(
    Output(ROLE_POPULATION_VALUE, "options"),
    Input(SPLIT_ROLE_POPULATION_DROPDOWN, "value"),
    State(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=False
)
def create_dp_split_role_dropdown(split_role_population_values, meta_data_filters, nets):
    if not split_role_population_values or not nets:
        return no_update
    query = generate_avail_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters,
        column_name=split_role_population_values,
        extra_columns=[split_role_population_values]
    )
    df, _ = run_query_with_nets_names_processing(query)
    options = [{"label": population, "value": population} for population in df[split_role_population_values]]
    return options


@callback(
    Output(PATH_NET_ACC_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input('acc-threshold-slider', 'value'),
    background=False,
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
        base_dists=slider_values
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy", role="host")


@callback(
    Output(PATH_NET_ACC_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input('acc-threshold-slider', 'value'),
    background=False,
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
        base_dists=slider_values
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy")


@callback(
    Output(PATH_NET_FALSES_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input('falses-threshold-slider', 'value'),
    background=False,
)
def get_path_net_falses_host(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update
    query = generate_path_net_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        "falses",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role=["'host'", "'unmatched-host'"],
        base_dists=slider_values
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "falses", role="host")


@callback(
    Output(PATH_NET_FALSES_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input('falses-threshold-slider', 'value'),
    background=False,
)
def get_path_net_falses_next(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update
    query = generate_path_net_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        "falses",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role=["'non-host'", "'unmatched-non-host'"],
        base_dists=slider_values
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "falses")


@callback(
    Output(PATH_NET_MISSES_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input('misses-threshold-slider', 'value'),
    background=False,
)
def get_path_net_misses_host(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update
    query = generate_path_net_query(
        nets[PATHNET_GT],
        nets["meta_data"],
        "misses",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role=["'host'", "'unmatched-host'"],
        base_dists=slider_values
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "misses", role="host")


@callback(
    Output(PATH_NET_MISSES_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
    Input('misses-threshold-slider', 'value'),
    background=False,
)
def get_path_net_misses_next(meta_data_filters, pathnet_filters, nets, slider_values):
    if not nets:
        return no_update
    query = generate_path_net_query(
        nets[PATHNET_GT],
        nets["meta_data"],
        "misses",
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role=["'non-host'", "'unmatched-non-host'"],
        base_dists=slider_values
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "misses", role="non-host")


@callback(
    Output({"out": "graph", "role": MATCH}, "children"),
    Input(NETS, "data"),
    State({"out": "graph", "role": MATCH}, "id"),
    background=False
)
def generate_conf_matrices_components(nets, id):
    if not nets:
        return []
    children = generate_matrices_layout(
        nets=nets,
        upper_diag_id={"type": PATH_NET_ALL_TPR, "role": id["role"]},
        lower_diag_id={"type": PATH_NET_HOST_TPR, "role": id["role"]},
        left_conf_mat_id={"type": PATH_NET_ALL_CONF_MATS, "role": id["role"]},
        right_conf_mat_id={"type": PATH_NET_HOST_CONF_MAT, "role": id["role"]}
    )
    return children


@callback(
    Output({"type": PATH_NET_ALL_TPR, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_ALL_CONF_MATS, "role": MATCH, "index": ALL}, "figure"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
    State({"type": PATH_NET_ALL_TPR, "role": MATCH}, "id"),
    Input(PATHNET_FILTERS, "data"),
    background=False,
)
def generate_overall_conf_matrices(nets, meta_data_filters, id, pathnet_filters):
    if not nets:
        return no_update
    role = id["role"]
    diagonal_compare, mats_figs = generate_matrices_graphs(
        pred_col=f"{role}_role",
        label_col=f"matched_{role}_role",
        nets_tables=nets[PATHNET_PRED],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=ROLE_CLASSES_NAMES[role],
        mat_name=f"{role} TPR for all dps",
        extra_filters=pathnet_filters
    )
    return diagonal_compare, mats_figs


@callback(
    Output({"type": PATH_NET_HOST_TPR, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_HOST_CONF_MAT, "index": ALL, "role": MATCH}, "figure"),
    Input(NETS, "data"),
    Input(MD_FILTERS, "data"),
    State({"type": PATH_NET_ALL_TPR, "role": MATCH}, "id"),
    Input(PATHNET_FILTERS, "data"),
    background=False
)
def generate_host_conf_matrices(nets, meta_data_filters, id, pathnet_filters):
    if not nets:
        return no_update
    if pathnet_filters:
        pathnet_filters = f"{pathnet_filters} AND role = 'host'"
    else:
        pathnet_filters = "role = 'host'"
    role = id["role"]
    diagonal_compare, mats_figs = generate_matrices_graphs(
        pred_col=f"{role}_role",
        label_col=f"matched_{role}_role",
        nets_tables=nets[PATHNET_PRED],
        meta_data_table=nets["meta_data"],
        net_names=nets["names"],
        meta_data_filters=meta_data_filters,
        class_names=ROLE_CLASSES_NAMES[role],
        mat_name=f"{role} TPR for host dp",
        extra_filters=pathnet_filters
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

    units = "(m)" if column == "bias" else "(s)"
    title = f"Distribution of {role} {column} {units}"

    return basic_histogram_plot(data, column, "overall", title=title, color="net_id")


@callback(
    Output(PATH_NET_BIASES_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    State(NETS, "data"),
    background=False,
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
    background=False,
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
    background=False,
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
    background=False,
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



"""
    SELECT net_id, split_role as split_role, matched_split_role as matched_split_role, COUNT(*) AS res_count
    FROM (
    SELECT * FROM
    (SELECT * FROM
    (SELECT clip_name, grabIndex, net_id, role, bin_population, smooth_index, "dist_0.5", "dist_1.0", "dist_1.5", "dist_2.0", "dist_2.5", "dist_3.0", "dist_3.5", "dist_4.0", "dist_4.5", "dist_5.0", split_role, matched_split_role FROM aaa4dc3d639fdb2c8196ae5a15be6da9394)
    WHERE (clip_name, grabIndex) IN (SELECT clip_name, grabIndex FROM aaa4dc3d639fdb2c8196ae5a15be6da9394)
    AND split_role != -1)
    INNER JOIN aaa90eabaf1f85f72f568e27c48306b6a1f USING (clip_name, grabIndex)
    WHERE TRUE 
    )
    GROUP BY net_id, split_role, matched_split_role
    
"""