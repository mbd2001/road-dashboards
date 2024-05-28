import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update
from road_database_toolkit.athena.athena_utils import query_athena

from road_eval_dashboard.road_dump_dashboard import COLUMNS_DICT, FILTERS_DICT
from road_eval_dashboard.road_dump_dashboard.components.constants.components_ids import (
    CHARTS_MAIN_TABLE,
    CHARTS_MD_TABLE,
    DYNAMIC_CHART,
    DYNAMIC_CHART_DROPDOWN,
    DYNAMIC_CHART_SLIDER,
    DYNAMIC_PERCENTAGE_SWITCH,
    GENERIC_COLUMNS_CHART,
    GENERIC_COLUMNS_SLIDER,
    GENERIC_FILTERS_CHART,
    GENERIC_PERCENTAGE_SWITCH,
    INTERSECTION_SWITCH,
    MD_FILTERS,
    OBJ_COUNT_CHART,
    OBJ_COUNT_PERCENTAGE_SWITCH,
    POPULATION_DROPDOWN,
    TABLES,
)
from road_eval_dashboard.road_dump_dashboard.components.dashboard_layout import card_wrapper, loading_wrapper
from road_eval_dashboard.road_dump_dashboard.components.logical_components import (
    DIFF_COL,
    generate_count_obj_query,
    generate_count_query,
    generate_dynamic_count_query,
    get_tables_property_union,
    get_value_from_tables_property_union,
)
from road_eval_dashboard.road_dump_dashboard.graphs import basic_histogram_plot, pie_or_line_wrapper


def exponent_transform(value, base=10):
    return base**value


def layout(main_table, meta_data_table=None, columns=None, filters=None):
    graphs_layout = html.Div(
        [
            html.Div(id=CHARTS_MAIN_TABLE, children=main_table, style={"display": "none"}),
            html.Div(id=CHARTS_MD_TABLE, children=meta_data_table, style={"display": "none"}),
            dynamic_chart_layout(),
            generic_charts_layout(GENERIC_COLUMNS_CHART, columns, GENERIC_PERCENTAGE_SWITCH, GENERIC_COLUMNS_SLIDER),
            generic_charts_layout(GENERIC_FILTERS_CHART, filters, GENERIC_PERCENTAGE_SWITCH),
            obj_count_layout() if meta_data_table else None,
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
            dbc.Row(get_single_graph_layout(DYNAMIC_CHART, DYNAMIC_PERCENTAGE_SWITCH, DYNAMIC_CHART_SLIDER)),
        ]
    )

    return dynamic_chart


def generic_charts_layout(graph_type, obj_ids, percentage_button_type, slider_type=None):
    if obj_ids is None:
        return

    list_ids_tuples = [tuple(obj_ids[i : i + 2]) for i in range(0, len(obj_ids), 2)]
    generic_filters_charts = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        card_wrapper(
                            get_single_graph_layout(
                                {"type": graph_type, "index": id},
                                {"type": percentage_button_type, "index": id},
                                {"type": slider_type, "index": id} if slider_type else None,
                            )
                        )
                    )
                    for id in ids_tuple
                ]
            )
            for ids_tuple in list_ids_tuples
        ]
    )
    return generic_filters_charts


def get_single_graph_layout(graph_id, percentage_button_id=None, slider_id=None):
    graph = loading_wrapper(
        dcc.Graph(
            id=graph_id,
            config={"displayModeBar": False},
        )
    )
    slider = (
        dcc.Slider(
            -2,
            3,
            0.1,
            id=slider_id,
            vertical=True,
            marks={i: "{}".format(exponent_transform(i)) for i in range(-2, 4)},
            value=0,
        )
        if slider_id
        else None
    )
    percentage_button = (
        daq.BooleanSwitch(
            id=percentage_button_id,
            on=False,
            label="Absolute <-> Percentage",
            labelPosition="top",
        )
        if percentage_button_id
        else None
    )
    col_layout = [
        dbc.Row([dbc.Col(graph, width=11), dbc.Col(slider, width=1)]) if slider is not None else graph,
        dbc.Row(percentage_button),
    ]
    return col_layout


@callback(
    Output(DYNAMIC_CHART_DROPDOWN, "options"),
    Input(TABLES, "data"),
    State(CHARTS_MAIN_TABLE, "children"),
)
def init_dynamic_chart_dropdown(tables, main_table):
    if not tables:
        return no_update

    columns_options = get_tables_property_union(tables[main_table])
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
    State(CHARTS_MAIN_TABLE, "children"),
    State(CHARTS_MD_TABLE, "children"),
)
def get_dynamic_chart(
    main_column,
    slider_value,
    compute_percentage,
    meta_data_filters,
    tables,
    population,
    intersection_on,
    main_table,
    meta_data_table,
):
    if not population or not tables or not main_column:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)
    fig = get_group_by_chart(
        main_tables,
        population,
        main_column,
        intersection_on,
        meta_data_tables,
        meta_data_filters,
        slider_value,
        compute_percentage,
    )
    return fig


@callback(
    Output({"type": GENERIC_COLUMNS_CHART, "index": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    State({"type": GENERIC_COLUMNS_CHART, "index": MATCH}, "id"),
    Input({"type": GENERIC_COLUMNS_SLIDER, "index": MATCH}, "value"),
    Input({"type": GENERIC_PERCENTAGE_SWITCH, "index": MATCH}, "on"),
    State(CHARTS_MAIN_TABLE, "children"),
    State(CHARTS_MD_TABLE, "children"),
)
def get_generic_column_chart(
    meta_data_filters,
    tables,
    population,
    intersection_on,
    column,
    slider_value,
    compute_percentage,
    main_table,
    meta_data_table,
):
    if not population or not tables:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)
    filters_name = column["index"]
    main_column, diff_column, extra_filters, graph_title = get_query_params(filters_name)
    fig = get_group_by_chart(
        main_tables,
        population,
        main_column,
        intersection_on,
        meta_data_tables,
        meta_data_filters,
        slider_value,
        diff_column,
        extra_filters,
        graph_title,
        compute_percentage,
    )
    return fig


@callback(
    Output(OBJ_COUNT_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    State(CHARTS_MAIN_TABLE, "children"),
    State(CHARTS_MD_TABLE, "children"),
    Input(OBJ_COUNT_PERCENTAGE_SWITCH, "on"),
)
def get_generic_column_chart(
    meta_data_filters,
    tables,
    population,
    intersection_on,
    main_table,
    meta_data_table,
    compute_percentage,
):
    if not population or not tables:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)
    query = generate_count_obj_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        compute_percentage=compute_percentage,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    title = get_graph_title(graph_title="Objects Count")
    y_col = "percentage" if compute_percentage else "overall"
    fig = basic_histogram_plot(data, "objects_per_frame", y_col, title=title)
    return fig


def get_query_params(filters_name):
    filters_dict = COLUMNS_DICT.get(filters_name)
    if filters_dict is None:
        return filters_name, None, None, None

    main_column = filters_dict.get("main_column")
    diff_column = filters_dict.get("diff_column")
    extra_filters = filters_dict.get("extra_filters")
    return main_column, diff_column, extra_filters, filters_name


def get_group_by_chart(
    main_tables,
    population,
    main_column,
    intersection_on,
    meta_data_tables=None,
    meta_data_filters=None,
    slider_value=None,
    diff_column=None,
    extra_filters=None,
    graph_title=None,
    compute_percentage=False,
):
    bins_factor = (
        None if slider_value is None else get_bins_factor(slider_value, main_column, main_tables, meta_data_tables)
    )
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        main_column=main_column,
        bins_factor=bins_factor,
        diff_column=diff_column,
        extra_filters=extra_filters,
        compute_percentage=compute_percentage,
    )
    y_col = "percentage" if compute_percentage else "overall"
    data, _ = query_athena(database="run_eval_db", query=query)
    title = get_graph_title(main_column, diff_column, graph_title)
    col_id = DIFF_COL if diff_column else main_column
    if data[col_id].nunique() > 16:
        fig = basic_histogram_plot(data, col_id, y_col, title=title)
    else:
        fig = pie_or_line_wrapper(data, col_id, y_col, title=title)
    return fig


def get_bins_factor(slider_value, column, main_tables, meta_data_tables):
    column_type = get_value_from_tables_property_union(column, main_tables, meta_data_tables, key_as_prefix=True)
    bins_factor = exponent_transform(slider_value) if column_type.startswith(("int", "float", "double")) else None
    return bins_factor


@callback(
    Output({"type": GENERIC_FILTERS_CHART, "index": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input({"type": GENERIC_PERCENTAGE_SWITCH, "index": MATCH}, "on"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    State({"type": GENERIC_FILTERS_CHART, "index": MATCH}, "id"),
    State(CHARTS_MAIN_TABLE, "children"),
    State(CHARTS_MD_TABLE, "children"),
)
def get_generic_filter_chart(
    meta_data_filters, compute_percentage, tables, population, intersection_on, filters, main_table, meta_data_table
):
    if not population or not tables:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)
    filters_name = filters["index"]
    filters = FILTERS_DICT[filters_name]
    query = generate_dynamic_count_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        interesting_filters=filters,
        compute_percentage=compute_percentage,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data = data.melt(id_vars=["dump_name"], var_name="filter", value_name="overall")
    title = get_graph_title(graph_title=filters_name)
    fig = pie_or_line_wrapper(data, "filter", "overall", title=title)
    return fig


def get_graph_title(main_column=None, diff_column=None, graph_title=None):
    if graph_title is not None:
        title = graph_title.title().replace("_", " ")
        return f"Distribution of {title}"

    title = main_column.title()
    title += f" and {diff_column.title()} diff" if diff_column is not None else ""
    title = title.replace("_", " ")
    return f"Distribution of {title}"
