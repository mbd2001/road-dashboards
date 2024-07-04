import json

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update, page_registry
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    DYNAMIC_CHART,
    DYNAMIC_CHART_DROPDOWN,
    DYNAMIC_CHART_SLIDER,
    DYNAMIC_PERCENTAGE_SWITCH,
    GENERIC_BINS_SLIDER,
    GENERIC_COUNT_CHART,
    GENERIC_COUNT_EXTRA_INFO,
    GENERIC_FILTER_IGNORES_SWITCH,
    GENERIC_PERCENTAGE_SWITCH,
    INTERSECTION_SWITCH,
    MD_FILTERS,
    OBJ_COUNT_CHART,
    OBJ_COUNT_PERCENTAGE_SWITCH,
    POPULATION_DROPDOWN,
    TABLES,
    URL,
)
from road_dashboards.road_dump_dashboard.components.constants.graphs_properties import (
    CasesGraphProperties,
    GroupByGraphProperties,
)
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.components.graph_wrappers.generic_grid import get_grid_layout
from road_dashboards.road_dump_dashboard.components.logical_components.queries_manager import (
    DIFF_COL,
    generate_count_obj_query,
    generate_count_query,
    get_tables_property_union,
)
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    get_value_from_tables_property_union,
)
from road_dashboards.road_dump_dashboard.graphs.histogram_plot import basic_histogram_plot
from road_dashboards.road_dump_dashboard.graphs.line_graph import draw_line_graph
from road_dashboards.road_dump_dashboard.graphs.pie_chart import basic_pie_chart


def exponent_transform(value, base=10):
    return base**value


def layout(group_by_graphs, cases_graphs=None, draw_obj_count=False):
    graphs_layout = html.Div(
        [
            dynamic_chart_layout(),
            get_grid_layout(group_by_graphs, group_by_chart_generator),
            get_grid_layout(cases_graphs, cases_chart_generator) if cases_graphs else None,
            obj_count_layout() if draw_obj_count is True else None,
        ]
    )
    return graphs_layout


def obj_count_layout():
    obj_count_chart = card_wrapper(dbc.Row(get_single_graph_layout(OBJ_COUNT_CHART, OBJ_COUNT_PERCENTAGE_SWITCH)))
    return obj_count_chart


def dynamic_chart_layout():
    dynamic_chart = card_wrapper(
        [
            dbc.Row(
                dcc.Dropdown(
                    id=DYNAMIC_CHART_DROPDOWN,
                    style={"minWidth": "100%"},
                    multi=False,
                    placeholder="Attribute",
                    value="",
                )
            ),
            dbc.Row(
                get_single_graph_layout(
                    DYNAMIC_CHART, DYNAMIC_PERCENTAGE_SWITCH, DYNAMIC_CHART_SLIDER, include_slider=True
                )
            ),
        ]
    )

    return dynamic_chart


def group_by_chart_generator(graph_properties: GroupByGraphProperties):
    index = graph_properties.name
    include_slider = graph_properties.include_slider
    slider_default_value = graph_properties.slider_default_value
    include_filter_ignores = bool(graph_properties.ignore_filter)
    chart_layout = get_single_graph_layout(
        {
            "type": GENERIC_COUNT_CHART,
            "index": index,
        },
        {"type": GENERIC_PERCENTAGE_SWITCH, "index": index},
        slider_id={"type": GENERIC_BINS_SLIDER, "index": index},
        filter_ignores_id={
            "type": GENERIC_FILTER_IGNORES_SWITCH,
            "index": index,
        },
        include_slider=include_slider,
        include_filter_ignores=include_filter_ignores,
        slider_default_value=slider_default_value,
        additional_info_id={"type": GENERIC_COUNT_EXTRA_INFO, "index": index},
        additional_info=json.dumps(
            {
                "name": graph_properties.name,
                "group_by_column": graph_properties.group_by_column,
                "diff_column": graph_properties.diff_column,
                "extra_columns": graph_properties.extra_columns,
                "ignore_filter": graph_properties.ignore_filter,
            }
        ),
    )
    return chart_layout


def cases_chart_generator(graph_properties: CasesGraphProperties):
    index = graph_properties.name
    include_filter_ignores = bool(graph_properties.ignore_filter)
    chart_layout = get_single_graph_layout(
        graph_id={
            "type": GENERIC_COUNT_CHART,
            "index": index,
        },
        percentage_button_id={"type": GENERIC_PERCENTAGE_SWITCH, "index": index},
        slider_id={"type": GENERIC_BINS_SLIDER, "index": index},
        filter_ignores_id={
            "type": GENERIC_FILTER_IGNORES_SWITCH,
            "index": index,
        },
        include_filter_ignores=include_filter_ignores,
        additional_info_id={"type": GENERIC_COUNT_EXTRA_INFO, "index": index},
        additional_info=json.dumps(
            {
                "name": graph_properties.name,
                "extra_columns": graph_properties.extra_columns,
                "interesting_cases": graph_properties.interesting_cases,
                "ignore_filter": graph_properties.ignore_filter,
            }
        ),
    )
    return chart_layout


def get_single_graph_layout(
    graph_id,
    percentage_button_id,
    slider_id=None,
    filter_ignores_id=None,
    include_slider=False,
    include_filter_ignores=True,
    slider_default_value=0,
    additional_info_id=None,
    additional_info=None,
):
    graph = loading_wrapper(
        dcc.Graph(
            id=graph_id,
            config={"displayModeBar": False},
        )
    )
    percentage_button = daq.BooleanSwitch(
        id=percentage_button_id,
        on=False,
        label="Absolute <-> Percentage",
        labelPosition="top",
    )
    slider = (
        dcc.Slider(
            -2,
            3,
            0.1,
            id=slider_id,
            vertical=True,
            marks={i: "{}".format(exponent_transform(i)) for i in range(-2, 4)},
            value=slider_default_value if include_slider else None,
        )
        if slider_id
        else None
    )
    filter_ignores_button = (
        daq.BooleanSwitch(
            id=filter_ignores_id,
            on=True,
            label="Show All <-> Filter Ignores",
            labelPosition="top",
        )
        if filter_ignores_id
        else None
    )
    if slider is not None and include_slider is True:
        graph_row = dbc.Row([dbc.Col(graph, width=11), dbc.Col(slider, width=1)])
    elif slider is not None:
        graph_row = dbc.Row([graph, html.Div(slider, hidden=True)])
    else:
        graph_row = dbc.Row(graph)

    if filter_ignores_button is not None and include_filter_ignores is True:
        buttons_row = dbc.Row([dbc.Col(percentage_button), dbc.Col(filter_ignores_button)])
    elif filter_ignores_button is not None:
        buttons_row = dbc.Row([dbc.Col([percentage_button, html.Div(filter_ignores_button, hidden=True)])])
    else:
        buttons_row = dbc.Row(dbc.Col(percentage_button))

    extra_info = (
        html.Div(id=additional_info_id, hidden=True, **{"data-graph": additional_info}) if additional_info_id else None
    )
    single_graph_layout = html.Div([graph_row, buttons_row, extra_info])
    return single_graph_layout


@callback(Output(DYNAMIC_CHART_DROPDOWN, "options"), Input(TABLES, "data"), State(URL, "pathname"))
def init_dynamic_chart_dropdown(tables, pathname):
    if not tables:
        return no_update

    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    main_tables = tables[page_properties["main_table"]]
    columns_options = get_tables_property_union(main_tables)
    return columns_options


@callback(
    Output(DYNAMIC_CHART, "figure"),
    Input(DYNAMIC_CHART_DROPDOWN, "value"),
    Input(DYNAMIC_CHART_SLIDER, "value"),
    Input(DYNAMIC_PERCENTAGE_SWITCH, "on"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    State(URL, "pathname"),
)
def get_dynamic_chart(
    main_column, slider_value, compute_percentage, meta_data_filters, tables, population, intersection_on, pathname
):
    if not population or not tables or not main_column:
        return no_update

    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    main_tables = tables[page_properties["main_table"]]
    meta_data_tables = tables.get(page_properties["meta_data_table"])
    column_type = get_column_type(main_column, main_tables, meta_data_tables=meta_data_tables)
    bins_factor = get_bins_factor(slider_value, column_type=column_type)
    fig = get_group_by_chart(
        main_tables,
        population,
        intersection_on,
        f"{main_column.title()} Distribution",
        [main_column],
        group_by_column=main_column,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        bins_factor=bins_factor,
        compute_percentage=compute_percentage,
    )
    return fig


@callback(
    Output({"type": GENERIC_COUNT_CHART, "index": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    State({"type": GENERIC_COUNT_EXTRA_INFO, "index": MATCH}, "data-graph"),
    Input({"type": GENERIC_BINS_SLIDER, "index": MATCH}, "value"),
    Input({"type": GENERIC_PERCENTAGE_SWITCH, "index": MATCH}, "on"),
    Input({"type": GENERIC_FILTER_IGNORES_SWITCH, "index": MATCH}, "on"),
    State(URL, "pathname"),
)
def get_generic_count_chart(
    meta_data_filters,
    tables,
    population,
    intersection_on,
    graph_properties,
    slider_value,
    compute_percentage,
    filter_ignores,
    pathname,
):
    if not population or not tables:
        return no_update

    page_name = pathname.strip("/")
    page_properties = page_registry[f"pages.{page_name}"]
    main_tables = tables[page_properties["main_table"]]
    meta_data_tables = tables.get(page_properties["meta_data_table"])

    bins_factor = get_bins_factor(slider_value)
    graph_properties = json.loads(graph_properties)
    fig = get_group_by_chart(
        main_tables,
        population,
        intersection_on,
        graph_properties["name"],
        graph_properties["extra_columns"],
        group_by_column=graph_properties.get("group_by_column"),
        diff_column=graph_properties.get("diff_column"),
        interesting_cases=graph_properties.get("interesting_cases"),
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        bins_factor=bins_factor,
        extra_filters=graph_properties["ignore_filter"] if filter_ignores else None,
        compute_percentage=compute_percentage,
    )
    return fig


@callback(
    Output(OBJ_COUNT_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    State(URL, "pathname"),
    Input(OBJ_COUNT_PERCENTAGE_SWITCH, "on"),
)
def get_obj_column_chart(
    meta_data_filters,
    tables,
    population,
    intersection_on,
    pathname,
    compute_percentage,
):
    if not population or not tables:
        return no_update

    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    main_tables = tables[page_properties["main_table"]]
    meta_data_tables = tables.get(page_properties["meta_data_table"])
    query = generate_count_obj_query(
        main_tables,
        population,
        intersection_on,
        ["clip_name", "grabindex"],
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        compute_percentage=compute_percentage,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    y_col = "percentage" if compute_percentage else "overall"
    graph_title = "Objects Count"
    fig = basic_histogram_plot(data, "objects_per_frame", y_col, title=graph_title)
    return fig


def get_group_by_chart(
    main_tables,
    population,
    intersection_on,
    graph_title,
    extra_columns,
    group_by_column=None,
    diff_column=None,
    interesting_cases=None,
    meta_data_tables=None,
    meta_data_filters=None,
    bins_factor=None,
    extra_filters=None,
    compute_percentage=False,
):
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        main_column=group_by_column,
        bins_factor=bins_factor,
        diff_column=diff_column,
        interesting_cases=interesting_cases,
        extra_columns=extra_columns,
        extra_filters=extra_filters,
        compute_percentage=compute_percentage,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    y_col = "percentage" if compute_percentage else "overall"
    col_id = DIFF_COL if diff_column else (group_by_column if group_by_column else "cases")
    if data[col_id].nunique() > 16:
        fig = basic_histogram_plot(data, col_id, y_col, title=graph_title)
    else:
        fig = pie_or_line_graph(data, col_id, y_col, title=graph_title)
    return fig


def pie_or_line_graph(data, names, values, title="", hover=None, color="dump_name"):
    if data[color].nunique() == 1:
        fig = basic_pie_chart(data, names, values, title=title, hover=hover)
    else:
        fig = draw_line_graph(data, names, values, title=title, hover=hover, color=color)

    return fig


def get_bins_factor(slider_value, column_type=None):
    if slider_value is None or (column_type is not None and not column_type.startswith(("int", "float", "double"))):
        return None

    bins_factor = exponent_transform(slider_value)
    return bins_factor


def get_column_type(column, main_tables, meta_data_tables=None):
    column_type = get_value_from_tables_property_union(column, main_tables, meta_data_tables)
    return column_type
