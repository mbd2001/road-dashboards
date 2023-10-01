import dash_bootstrap_components as dbc
from dash import html, dcc, register_page, Input, Output, callback, State, no_update

from road_eval_dashboard.components import (
    meta_data_filter,
    base_dataset_statistics,
)
from road_eval_dashboard.components.components_ids import (
    PATH_NET_ACC_HOST,
    PATH_NET_ACC_NEXT,
    PATH_NET_FALSES_HOST,
    PATH_NET_FALSES_NEXT,
    MD_FILTERS,
    NETS,
)
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.components.queries_manager import (
    generate_path_net_query,
    distances,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/path_net", name="Path Net", order=9, **extra_properties.__dict__)

layout = html.Div(
    [
        html.H1("Path Net Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.dp_layout,
        card_wrapper(
            [
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
    ]
)


@callback(
    Output(PATH_NET_ACC_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_path_net_acc_host(meta_data_filters, nets):
    if not nets:
        return no_update

    query = generate_path_net_query(
        nets["dp_tables"],
        nets["meta_data"],
        "acc",
        meta_data_filters=meta_data_filters,
        role="host",
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy", role="host")


@callback(
    Output(PATH_NET_ACC_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_path_net_acc_next(meta_data_filters, nets):
    if not nets:
        return no_update

    query = generate_path_net_query(
        nets["dp_tables"], nets["meta_data"], "acc", meta_data_filters=meta_data_filters, role="non-host"
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "accuracy")


@callback(
    Output(PATH_NET_FALSES_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_path_net_falses_host(meta_data_filters, nets):
    if not nets:
        return no_update

    query = generate_path_net_query(
        nets["dp_tables"],
        nets["meta_data"],
        "falses",
        meta_data_filters=meta_data_filters,
        role="host",
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "falses", role="host")


@callback(
    Output(PATH_NET_FALSES_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_path_net_falses_next(meta_data_filters, nets):
    if not nets:
        return no_update

    query = generate_path_net_query(
        nets["dp_tables"], nets["meta_data"], "falses", meta_data_filters=meta_data_filters, role="non-host"
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, distances, "falses")
