import dash_bootstrap_components as dbc
from dash import html, register_page, dcc, callback, Output, Input, State, no_update

from road_dump_dashboard.components import meta_data_filter, base_dataset_statistics
from road_dump_dashboard.components.components_ids import (
    MD_FILTERS,
    POPULATION_DROPDOWN,
    LM_COLOR_PIE_CHART,
    LM_ROLE_PIE_CHART,
    INTERSECTION_SWITCH,
    TABLES,
    LM_DYNAMIC_PIE_CHART_SLIDER,
    LM_DYNAMIC_PIE_CHART,
    LM_DYNAMIC_PIE_CHART_DROPDOWN,
    LM_TYPE_PIE_CHART,
)
from road_dump_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_dump_dashboard.components.page_properties import PageProperties
from road_dump_dashboard.components.queries_manager import (
    generate_count_query,
)
from road_dump_dashboard.graphs.histogram_plot import basic_histogram_plot
from road_database_toolkit.athena.athena_utils import query_athena
from road_dump_dashboard.graphs.pie_or_line_wrapper import pie_or_line_wrapper

extra_properties = PageProperties("search")
register_page(__name__, path="/lane_mark", name="Lane Mark", order=2, **extra_properties.__dict__)


def exponent_transform(value, base=10):
    return base**value


layout = html.Div(
    [
        html.H1("Lane Mark", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.lm_layout,
        card_wrapper(
            [
                dbc.Row(
                    dcc.Dropdown(
                        id=LM_DYNAMIC_PIE_CHART_DROPDOWN,
                        style={"minWidth": "100%"},
                        multi=False,
                        placeholder="Attribute",
                        value="",
                    ),
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=LM_DYNAMIC_PIE_CHART, config={"displayModeBar": False})]),
                            width=11,
                        ),
                        dbc.Col(
                            dcc.Slider(
                                -2,
                                3,
                                0.1,
                                id=LM_DYNAMIC_PIE_CHART_SLIDER,
                                vertical=True,
                                marks={i: "{}".format(exponent_transform(i)) for i in range(-2, 4)},
                                value=-1,
                            ),
                            width=1,
                        ),
                    ]
                ),
            ]
        ),
        dbc.Row(card_wrapper([loading_wrapper([dcc.Graph(id=LM_TYPE_PIE_CHART, config={"displayModeBar": False})])])),
        dbc.Row(
            [
                dbc.Col(
                    card_wrapper(
                        [loading_wrapper([dcc.Graph(id=LM_COLOR_PIE_CHART, config={"displayModeBar": False})])]
                    ),
                    width=6,
                ),
                dbc.Col(
                    card_wrapper(
                        [loading_wrapper([dcc.Graph(id=LM_ROLE_PIE_CHART, config={"displayModeBar": False})])]
                    ),
                    width=6,
                ),
            ],
        ),
    ]
)


@callback(
    Output(LM_ROLE_PIE_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_lm_role_pie_chart(meta_data_filters, tables, population, intersection_on):
    if not population or not tables:
        return no_update

    main_tables = tables["lm_meta_data"]
    meta_data_tables = tables["meta_data"]
    group_by_column = "vert_role"
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        group_by_column=group_by_column,
        extra_columns=[group_by_column],
        extra_filters=f" {group_by_column} != 'ROLE_IGNORE' AND {group_by_column} != 'IRRELEVANT' ",
    )
    print(query)
    data, _ = query_athena(database="run_eval_db", query=query)
    title = f"Distribution of Lane Marks Roles"
    fig = pie_or_line_wrapper(data, group_by_column, "overall", title=title)
    return fig


@callback(
    Output(LM_COLOR_PIE_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_lm_color_pie_chart(meta_data_filters, tables, population, intersection_on):
    if not population or not tables:
        return no_update

    main_tables = tables["lm_meta_data"]
    meta_data_tables = tables["meta_data"]
    group_by_column = "vert_color"
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        group_by_column=group_by_column,
        extra_columns=[group_by_column],
        extra_filters=f" {group_by_column} != 'ignore' ",
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    title = f"Distribution of Lane Marks Color"
    fig = pie_or_line_wrapper(data, group_by_column, "overall", title=title)
    return fig


@callback(
    Output(LM_TYPE_PIE_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_lm_type_pie_chart(meta_data_filters, tables, population, intersection_on):
    if not population or not tables:
        return no_update

    main_tables = tables["lm_meta_data"]
    meta_data_tables = tables["meta_data"]
    group_by_column = "vert_type"
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        group_by_column=group_by_column,
        extra_columns=[group_by_column],
        extra_filters=f" {group_by_column} != 'ignore' ",
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    title = f"Distribution of Lane Marks Type"
    fig = pie_or_line_wrapper(data, group_by_column, "overall", title=title)
    return fig


@callback(
    Output(LM_DYNAMIC_PIE_CHART_DROPDOWN, "options"),
    Input(TABLES, "data"),
)
def init_pie_dropdown(tables):
    if not tables:
        return no_update

    columns_options = tables["lm_meta_data"]["columns_options"] + tables["meta_data"]["columns_options"]
    return columns_options


@callback(
    Output(LM_DYNAMIC_PIE_CHART, "figure"),
    Input(LM_DYNAMIC_PIE_CHART_DROPDOWN, "value"),
    Input(LM_DYNAMIC_PIE_CHART_SLIDER, "value"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_dynamic_pie_chart(group_by_column, slider_value, meta_data_filters, tables, population, intersection_on):
    if not population or not tables or not group_by_column:
        return no_update

    main_tables = tables["lm_meta_data"]
    meta_data_tables = tables["meta_data"]
    column_type = tables["lm_meta_data"]["columns_to_type"].get(group_by_column) or tables["meta_data"][
        "columns_to_type"
    ].get(group_by_column)
    bins_factor = None
    ignore_filter = ""
    if column_type.startswith(("int", "float", "double")):
        bin_size = exponent_transform(slider_value)
        bins_factor = bin_size
        ignore_filter = f"{group_by_column} <> 999 AND {group_by_column} <> -999"

    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=" AND ".join(filter_str for filter_str in [meta_data_filters, ignore_filter] if filter_str),
        group_by_column=group_by_column,
        bins_factor=bins_factor,
        extra_columns=[group_by_column],
    )
    print(query)
    data, _ = query_athena(database="run_eval_db", query=query)
    title = f"Distribution of {group_by_column.replace('mdbi_', '').replace('_', ' ').title()}"

    if data[group_by_column].nunique() > 16:
        fig = basic_histogram_plot(data, group_by_column, "overall", title=title, color="dump_name")
    else:
        fig = pie_or_line_wrapper(data, group_by_column, "overall", title=title)
    return fig
