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
    CHARTS_MAIN_TABLE,
    CHARTS_MD_TABLE,
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


def layout(main_table, meta_data_table=None, columns=None, filters=None):
    if columns == None:
        columns = []

    if filters == None:
        filters = []

    graphs_layout = html.Div(
        [
            html.Div(id=CHARTS_MAIN_TABLE, children=main_table, style={"display": "none"}),
            html.Div(id=CHARTS_MD_TABLE, children=meta_data_table, style={"display": "none"}),
            dynamic_chart_layout(),
            *generic_charts_layout(GENERIC_COLUMNS_CHART, columns),
            *generic_charts_layout(GENERIC_FILTERS_CHART, filters),
        ]
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


def generic_charts_layout(obj_type, obj_ids):
    if not obj_ids:
        return [None]

    list_ids_tuples = [tuple(obj_ids[i : i + 2]) for i in range(0, len(obj_ids), 2)]
    generic_filters_charts = [
        dbc.Row(
            [
                dbc.Col(
                    card_wrapper(
                        [
                            loading_wrapper(
                                [
                                    dcc.Graph(
                                        id={"type": obj_type, "index": id},
                                        config={"displayModeBar": False},
                                    )
                                ]
                            )
                        ]
                    )
                )
                for id in ids_tuple
            ]
        )
        for ids_tuple in list_ids_tuples
    ]

    return generic_filters_charts


@callback(
    Output(DYNAMIC_CHART_DROPDOWN, "options"),
    Input(TABLES, "data"),
    State(CHARTS_MAIN_TABLE, "children"),
    State(CHARTS_MD_TABLE, "children"),
)
def init_dynamic_chart_dropdown(tables, main_table, meta_data_table):
    if not tables:
        return no_update

    columns_options = tables[main_table]["columns_options"] + (
        tables[meta_data_table]["columns_options"] if meta_data_table else []
    )
    return columns_options


@callback(
    Output(DYNAMIC_CHART, "figure"),
    Input(DYNAMIC_CHART_DROPDOWN, "value"),
    Input(DYNAMIC_CHART_SLIDER, "value"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    State(CHARTS_MAIN_TABLE, "children"),
    State(CHARTS_MD_TABLE, "children"),
    background=True,
)
def get_dynamic_chart(
    group_by_column, slider_value, meta_data_filters, tables, population, intersection_on, main_table, meta_data_table
):
    if not population or not tables or not group_by_column:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)

    column_type = main_tables["columns_to_type"].get(group_by_column) or meta_data_tables["columns_to_type"].get(
        group_by_column
    )
    ignore_str = get_ignore_str_from_column_type(group_by_column, column_type)
    bins_factor = (
        exponent_transform(slider_value) if column_type.startswith(("int", "float", "double")) else slider_value
    )
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
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
    State({"type": GENERIC_COLUMNS_CHART, "index": MATCH}, "id"),
    State(CHARTS_MAIN_TABLE, "children"),
    State(CHARTS_MD_TABLE, "children"),
    background=True,
)
def get_generic_column_chart(
    meta_data_filters, tables, population, intersection_on, col_to_compare, main_table, meta_data_table
):
    if not population or not tables:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)
    col_to_compare = col_to_compare["index"]

    column_type = main_tables["columns_to_type"].get(col_to_compare) or meta_data_tables["columns_to_type"].get(
        col_to_compare
    )
    ignore_str = get_ignore_str_from_column_type(col_to_compare, column_type)
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
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
    State({"type": GENERIC_FILTERS_CHART, "index": MATCH}, "id"),
    State(CHARTS_MAIN_TABLE, "children"),
    State(CHARTS_MD_TABLE, "children"),
    background=True,
)
def get_generic_filter_chart(
    meta_data_filters, tables, population, intersection_on, filters, main_table, meta_data_table
):
    if not population or not tables:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)
    filters_name = filters["index"]
    filters = FILTERS[filters_name]
    query = generate_dynamic_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        interesting_filters=filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data = data.melt(id_vars=["dump_name"], var_name="filter", value_name="overall")
    title = f"Distribution of {filters_name.title()}"
    fig = pie_or_line_wrapper(data, "filter", "overall", title=title)
    return fig


def get_ignore_str_from_column_type(column, column_type):
    if column_type.startswith(("int", "float", "double")):
        ignore_filter = f"{column} <> 999 AND {column} <> -999"
    elif column_type.startswith("object"):
        ignore_filter = f"{column} != 'ignore' AND {column} != 'Unknown'"
    else:
        ignore_filter = ""

    return ignore_filter
