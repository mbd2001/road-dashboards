import pickle as pkl

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, Patch, State, callback, dcc, html, no_update, page_registry
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    DISPLAY_CONF_MATS,
    DYNAMIC_CONF_DROPDOWN,
    DYNAMIC_CONF_MAT,
    DYNAMIC_SHOW_DIFF_BTN,
    GENERIC_CONF_EXTRA_INFO,
    GENERIC_CONF_MAT,
    GENERIC_FILTER_IGNORES_BTN,
    GENERIC_SHOW_DIFF_BTN,
    MAIN_NET_DROPDOWN,
    MD_FILTERS,
    POPULATION_DROPDOWN,
    SECONDARY_NET_DROPDOWN,
    TABLES,
    URL,
)
from road_dashboards.road_dump_dashboard.components.constants.graphs_properties import ConfMatGraphProperties
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.components.graph_wrappers import frames_carousel
from road_dashboards.road_dump_dashboard.components.graph_wrappers.generic_grid import get_grid_layout
from road_dashboards.road_dump_dashboard.components.logical_components.queries_manager import generate_conf_mat_query
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    get_tables_property_union,
)
from road_dashboards.road_dump_dashboard.graphs.confusion_matrix import get_confusion_matrix


def layout(graphs_properties):
    matrices_layout = html.Div(
        id=DISPLAY_CONF_MATS,
        children=[
            card_wrapper(
                [
                    nets_selection_layout(),
                    dynamic_conf_mat_layout(),
                    get_grid_layout(graphs_properties, conf_mat_graph_generator),
                ]
            ),
            frames_carousel.layout(),
        ],
        style={"display": "none"},
    )
    return matrices_layout


def nets_selection_layout():
    nets_selection = dbc.Row(
        [
            dbc.Col(
                dcc.Dropdown(
                    id=MAIN_NET_DROPDOWN,
                    style={"minWidth": "100%"},
                    multi=False,
                    placeholder="----",
                    value="",
                )
            ),
            dbc.Col(
                dcc.Dropdown(
                    id=SECONDARY_NET_DROPDOWN,
                    style={"minWidth": "100%"},
                    multi=False,
                    placeholder="----",
                    value="",
                )
            ),
        ]
    )

    return nets_selection


def conf_mat_graph_generator(graph_properties: ConfMatGraphProperties):
    index = graph_properties.name
    include_filter_ignores = bool(graph_properties.ignore_filter)
    conf_mat_layout = (
        get_single_mat_layout(
            {"type": GENERIC_CONF_MAT, "index": index},
            {"type": GENERIC_SHOW_DIFF_BTN, "index": index},
            filter_ignores_id={"type": GENERIC_FILTER_IGNORES_BTN, "index": index},
            include_filter_ignores=include_filter_ignores,
            additional_info_id={"type": GENERIC_CONF_EXTRA_INFO, "index": index},
            additional_info=graph_properties,
        ),
    )
    return conf_mat_layout


def dynamic_conf_mat_layout():
    dynamic_conf_mat = dbc.Row(
        [
            dcc.Dropdown(
                id=DYNAMIC_CONF_DROPDOWN,
                multi=False,
                placeholder="----",
                value="",
            ),
            get_single_mat_layout(DYNAMIC_CONF_MAT, DYNAMIC_SHOW_DIFF_BTN),
        ]
    )

    return dynamic_conf_mat


def get_single_mat_layout(
    mat_id,
    diff_btn_id,
    filter_ignores_id=None,
    include_filter_ignores=True,
    additional_info_id=None,
    additional_info=None,
):
    mat_row = dbc.Row(
        loading_wrapper(
            dcc.Graph(
                id=mat_id,
                config={"displayModeBar": False},
            )
        )
    )
    draw_diff_button = dbc.Button(
        "Draw Diff Frames",
        id=diff_btn_id,
        className="bg-primary mt-5",
    )
    filter_ignores_button = (
        daq.BooleanSwitch(
            id=filter_ignores_id,
            on=False,
            label="Show All <-> Filter Ignores",
            labelPosition="top",
        )
        if filter_ignores_id
        else None
    )

    if filter_ignores_button is not None and include_filter_ignores is True:
        buttons_row = dbc.Row([dbc.Col(draw_diff_button), dbc.Col(filter_ignores_button)])
    elif filter_ignores_button is not None:
        buttons_row = dbc.Row([dbc.Col([draw_diff_button, html.Div(filter_ignores_button, hidden=True)])])
    else:
        buttons_row = dbc.Row(dbc.Col(draw_diff_button))

    extra_info = (
        html.Div(id=additional_info_id, hidden=True, **{"data-graph": pkl.dumps(additional_info).hex()})
        if additional_info_id
        else None
    )
    single_mat_layout = html.Div([mat_row, buttons_row, extra_info])
    return single_mat_layout


@callback(
    Output(DISPLAY_CONF_MATS, "style"),
    Input(TABLES, "data"),
)
def init_dumps_dropdown(tables):
    if not tables or len(tables["names"]) <= 1:
        return no_update

    patched_style = Patch()
    patched_style["display"] = "block"
    return patched_style


@callback(
    Output(MAIN_NET_DROPDOWN, "options"),
    Output(MAIN_NET_DROPDOWN, "label"),
    Output(MAIN_NET_DROPDOWN, "value"),
    Output(SECONDARY_NET_DROPDOWN, "options"),
    Output(SECONDARY_NET_DROPDOWN, "label"),
    Output(SECONDARY_NET_DROPDOWN, "value"),
    Input(TABLES, "data"),
)
def init_dumps_dropdown(tables):
    if not tables:
        return no_update, no_update, no_update, no_update, no_update, no_update

    options = [{"label": name.title(), "value": name} for name in tables["names"]]
    if len(options) < 2:
        return options, options[0]["label"], options[0]["value"], no_update, no_update, no_update

    return options, options[0]["label"], options[0]["value"], options, options[1]["label"], options[1]["value"]


@callback(
    Output({"type": GENERIC_CONF_MAT, "index": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    State({"type": GENERIC_CONF_EXTRA_INFO, "index": MATCH}, "data-graph"),
    Input({"type": GENERIC_FILTER_IGNORES_BTN, "index": MATCH}, "on"),
    State(URL, "pathname"),
)
def get_generic_conf_mat(
    meta_data_filters, tables, population, main_dump, secondary_dump, graph_properties, filter_ignores, pathname
):
    if not population or not tables or not main_dump or not secondary_dump or main_dump == secondary_dump:
        return no_update

    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    main_tables = tables[page_properties["main_table"]]
    meta_data_tables = tables.get(page_properties["meta_data_table"])

    fig = get_conf_mat_fig(
        main_tables,
        graph_properties["column_to_compare"],
        graph_properties["extra_columns"],
        main_dump,
        secondary_dump,
        population,
        graph_properties["name"],
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=graph_properties["ignore_filter"] if filter_ignores else None,
    )
    return fig


@callback(
    Output(DYNAMIC_CONF_DROPDOWN, "options"),
    Input(TABLES, "data"),
    State(URL, "pathname"),
)
def init_dynamic_conf_dropdown(tables, pathname):
    if not tables:
        return no_update

    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    main_tables = tables[page_properties["main_table"]]
    columns_options = get_tables_property_union(main_tables)
    return columns_options


@callback(
    Output(DYNAMIC_CONF_MAT, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    Input(DYNAMIC_CONF_DROPDOWN, "value"),
    State(URL, "pathname"),
)
def get_dynamic_conf_mat(meta_data_filters, tables, population, main_dump, secondary_dump, dynamic_col, pathname):
    if (
        not population
        or not tables
        or not main_dump
        or not secondary_dump
        or not dynamic_col
        or main_dump == secondary_dump
    ):
        return no_update

    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    main_tables = tables[page_properties["main_table"]]
    meta_data_tables = tables.get(page_properties["meta_data_table"])
    column_to_compare = dynamic_col
    extra_columns = [column_to_compare]
    graph_title = f"{column_to_compare.title()} Classification"
    fig = get_conf_mat_fig(
        main_tables,
        column_to_compare,
        extra_columns,
        main_dump,
        secondary_dump,
        population,
        graph_title,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
    )
    return fig


def get_conf_mat_fig(
    main_tables,
    column_to_compare,
    extra_columns,
    main_dump,
    secondary_dump,
    population,
    graph_title,
    meta_data_tables=None,
    meta_data_filters=None,
    extra_filters=None,
):
    query = generate_conf_mat_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        column_to_compare,
        extra_columns,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    fig = get_confusion_matrix(data, x_label=secondary_dump, y_label=main_dump, title=graph_title)
    return fig
