import dash_bootstrap_components as dbc
from dash import html, register_page, dcc, callback, Output, Input, State, no_update, MATCH

from road_dump_dashboard.components.constants.common_filters import FILTERS
from road_dump_dashboard.components.constants.components_ids import (
    MD_FILTERS,
    POPULATION_DROPDOWN,
    INTERSECTION_SWITCH,
    TABLES,
    DYNAMIC_CHART_DROPDOWN,
    DYNAMIC_CHART,
    DYNAMIC_CHART_SLIDER,
    GENERIC_FILTERS_CHART,
    GENERIC_COLUMNS_CHART,
)
from road_dump_dashboard.components.dashboard_layout.layout_wrappers import loading_wrapper, card_wrapper
from road_dump_dashboard.components.logical_components.queries_manager import (
    generate_count_query,
    generate_dynamic_count_query,
)
from road_dump_dashboard.graphs.histogram_plot import basic_histogram_plot
from road_dump_dashboard.graphs.pie_or_line_wrapper import pie_or_line_wrapper
from road_database_toolkit.athena.athena_utils import query_athena


def exponent_transform(value, base=10):
    return base**value


def layout(columns=None, filters=None):
    if columns == None:
        columns = []

    if filters == None:
        filters = []

    graphs_layout = html.Div(
        [dynamic_chart_layout(), *generic_columns_charts_layout(columns), *generic_filters_charts_layout(filters)]
    )
    return graphs_layout


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
                [
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=DYNAMIC_CHART, config={"displayModeBar": False})]),
                        width=11,
                    ),
                    dbc.Col(
                        dcc.Slider(
                            -2,
                            3,
                            0.1,
                            id=DYNAMIC_CHART_SLIDER,
                            vertical=True,
                            marks={i: "{}".format(exponent_transform(i)) for i in range(-2, 4)},
                            value=-1,
                        ),
                        width=1,
                    ),
                ]
            ),
        ]
    )

    return dynamic_chart


def generic_columns_charts_layout(columns):
    if not columns:
        return [None]

    columns_iterator = iter(columns)
    list_columns_tuple = zip(columns_iterator, columns_iterator)
    generic_filters_charts = [
        dbc.Row(
            [
                dbc.Col(
                    card_wrapper(
                        [
                            loading_wrapper(
                                [
                                    dcc.Graph(
                                        id={"type": GENERIC_COLUMNS_CHART, "index": column},
                                        config={"displayModeBar": False},
                                    )
                                ]
                            )
                        ]
                    )
                )
                for column in columns_tuple
            ]
        )
        for columns_tuple in list_columns_tuple
    ]

    return generic_filters_charts


def generic_filters_charts_layout(filters):
    if not filters:
        return [None]

    filters_iterator = iter(filters)
    list_filters_tuple = zip(filters_iterator, filters_iterator)
    generic_filters_charts = [
        dbc.Row(
            [
                dbc.Col(
                    card_wrapper(
                        [
                            loading_wrapper(
                                [
                                    dcc.Graph(
                                        id={"type": GENERIC_FILTERS_CHART, "index": filter},
                                        config={"displayModeBar": False},
                                    )
                                ]
                            )
                        ]
                    )
                )
                for filter in filters_tuple
            ]
        )
        for filters_tuple in list_filters_tuple
    ]

    return generic_filters_charts


@callback(
    Output(DYNAMIC_CHART_DROPDOWN, "options"),
    Input(TABLES, "data"),
)
def init_dynamic_chart_dropdown(tables):
    if not tables:
        return no_update

    columns_options = tables["meta_data"]["columns_options"]
    return columns_options


@callback(
    Output(DYNAMIC_CHART, "figure"),
    Input(DYNAMIC_CHART_DROPDOWN, "value"),
    Input(DYNAMIC_CHART_SLIDER, "value"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_dynamic_chart(group_by_column, slider_value, meta_data_filters, tables, population, intersection_on):
    if not population or not tables or not group_by_column:
        return no_update

    main_tables = tables["meta_data"]

    column_type = tables["meta_data"]["columns_to_type"].get(group_by_column)
    ignore_str = get_ignore_str_from_column_type(column_type)
    bins_factor = (
        exponent_transform(slider_value) if column_type.startswith(("int", "float", "double")) else slider_value
    )
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters,
        group_by_column=group_by_column,
        bins_factor=bins_factor,
        extra_filters=ignore_str,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    title = f"Distribution of {group_by_column.replace('mdbi_', '').replace('_', ' ').title()}"

    if data[group_by_column].nunique() > 16:
        fig = basic_histogram_plot(data, group_by_column, "overall", title=title, color="dump_name")
    else:
        fig = pie_or_line_wrapper(data, group_by_column, "overall", title=title)
    return fig


@callback(
    Output({"type": GENERIC_COLUMNS_CHART, "index": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    Input({"type": GENERIC_COLUMNS_CHART, "index": MATCH}, "id"),
    background=True,
)
def get_generic_column_chart(meta_data_filters, tables, population, intersection_on, col_to_compare):
    if not population or not tables:
        return no_update

    main_tables = tables["meta_data"]
    col_to_compare = col_to_compare["index"]

    column_type = tables["meta_data"]["columns_to_type"].get(col_to_compare)
    ignore_str = get_ignore_str_from_column_type(column_type)
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters,
        group_by_column=col_to_compare,
        extra_filters=ignore_str,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    title = f"Distribution of {col_to_compare.title()}"
    fig = pie_or_line_wrapper(data, col_to_compare, "overall", title=title)
    return fig


@callback(
    Output({"type": GENERIC_FILTERS_CHART, "index": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    Input({"type": GENERIC_FILTERS_CHART, "index": MATCH}, "id"),
    background=True,
)
def get_generic_filter_chart(meta_data_filters, tables, population, intersection_on, filters):
    if not population or not tables:
        return no_update

    main_tables = tables["meta_data"]
    filters_name = filters["index"]
    filters = FILTERS[filters_name]
    query = generate_dynamic_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters,
        interesting_filters=filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data = data.melt(id_vars=["dump_name"], var_name="filter", value_name="overall")
    title = f"Distribution of {filters_name.title()}"
    fig = pie_or_line_wrapper(data, "filter", "overall", title=title)
    return fig


def get_ignore_str_from_column_type(column_type):
    if column_type.startswith(("int", "float", "double")):
        ignore_filter = f"{column_type} <> 999 AND {column_type} <> -999"
    elif column_type.startswith("object"):
        ignore_filter = f"{column_type} != 'ignore' AND {column_type} != 'Unknown'"
    else:
        ignore_filter = ""

    return ignore_filter
