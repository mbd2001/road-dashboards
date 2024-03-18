import dash_bootstrap_components as dbc
from dash import html, register_page, dcc, callback, Output, Input, State, ALL, no_update

from road_dump_dashboard.components import meta_data_filter, base_dataset_statistics
from road_dump_dashboard.components.common_filters import (
    ROAD_TYPE_FILTERS,
    LANE_MARK_COLOR_FILTERS,
)
from road_dump_dashboard.components.components_ids import (
    MD_FILTERS,
    POPULATION_DROPDOWN,
    DYNAMIC_PIE_CHART,
    DYNAMIC_PIE_CHART_DROPDOWN,
    TVGT_PIE_CHART,
    COUNTRIES_HEAT_MAP,
    MD_COLUMNS_OPTION,
    MD_COLUMNS_TO_TYPE,
    ROAD_TYPE_PIE_CHART,
    LANE_MARK_COLOR_PIE_CHART,
    GTEM_PIE_CHART,
    DYNAMIC_PIE_CHART_SLIDER,
    INTERSECTION_SWITCH,
    DUMPS,
    COUNTRIES_DROPDOWN,
    SECONDARY_NET_DROPDOWN,
    MAIN_NET_DROPDOWN,
    COMPARE_MATRICES,
    TVGT_CONF_MAT,
    GTEM_CONF_MAT,
)
from road_dump_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_dump_dashboard.components.page_properties import PageProperties
from road_dump_dashboard.components.queries_manager import (
    generate_count_query,
    generate_dynamic_count_query,
    generate_conf_mat_query,
)
from road_dump_dashboard.graphs.confusion_matrix import get_confusion_matrix
from road_dump_dashboard.graphs.countries_map import (
    generate_world_map,
    normalize_countries_names,
    iso_alpha_from_name,
    normalize_countries_count_to_percentiles,
)
from road_dump_dashboard.graphs.histogram_plot import basic_histogram_plot
from road_database_toolkit.athena.athena_utils import query_athena
from road_dump_dashboard.graphs.pie_or_line_wrapper import pie_or_line_wrapper

extra_properties = PageProperties("search")
register_page(__name__, path="/data_exploration", name="Data Exploration", order=1, **extra_properties.__dict__)


def exponent_transform(value, base=10):
    return base**value


layout = html.Div(
    [
        html.H1("Data Exploration", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        card_wrapper(
            [
                dbc.Row(
                    dcc.Dropdown(
                        id=DYNAMIC_PIE_CHART_DROPDOWN,
                        style={"minWidth": "100%"},
                        multi=False,
                        placeholder="Attribute",
                        value="",
                    ),
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=DYNAMIC_PIE_CHART, config={"displayModeBar": False})]),
                            width=11,
                        ),
                        dbc.Col(
                            dcc.Slider(
                                -2,
                                3,
                                0.1,
                                id=DYNAMIC_PIE_CHART_SLIDER,
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
        dbc.Row(
            [
                dbc.Col(
                    card_wrapper([loading_wrapper([dcc.Graph(id=TVGT_PIE_CHART, config={"displayModeBar": False})])]),
                    width=6,
                ),
                dbc.Col(
                    card_wrapper([loading_wrapper([dcc.Graph(id=GTEM_PIE_CHART, config={"displayModeBar": False})])]),
                    width=6,
                ),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    card_wrapper(
                        [loading_wrapper([dcc.Graph(id=ROAD_TYPE_PIE_CHART, config={"displayModeBar": False})])]
                    ),
                    width=6,
                ),
                dbc.Col(
                    card_wrapper(
                        [loading_wrapper([dcc.Graph(id=LANE_MARK_COLOR_PIE_CHART, config={"displayModeBar": False})])]
                    ),
                    width=6,
                ),
            ],
        ),
        html.Div(id=COMPARE_MATRICES),
        card_wrapper(
            [
                dbc.Row(
                    dcc.Dropdown(
                        id=COUNTRIES_DROPDOWN,
                        style={"minWidth": "100%"},
                        multi=False,
                        placeholder="----",
                        value="",
                    ),
                ),
                dbc.Row(loading_wrapper([dcc.Graph(id=COUNTRIES_HEAT_MAP, config={"displayModeBar": False})])),
            ]
        ),
    ]
)


@callback(
    Output(COMPARE_MATRICES, "children"),
    Input(DUMPS, "data"),
)
def init_matrices_layout(dumps):
    if not dumps:
        return []

    matrices_layout = (
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Dropdown(
                                id=MAIN_NET_DROPDOWN,
                                style={"minWidth": "100%"},
                                multi=False,
                                placeholder="----",
                                value="",
                            ),
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id=SECONDARY_NET_DROPDOWN,
                                style={"minWidth": "100%"},
                                multi=False,
                                placeholder="----",
                                value="",
                            ),
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(loading_wrapper([dcc.Graph(id=TVGT_CONF_MAT, config={"displayModeBar": False})])),
                        dbc.Col(loading_wrapper([dcc.Graph(id=GTEM_CONF_MAT, config={"displayModeBar": False})])),
                    ]
                ),
            ]
        ),
    )

    return matrices_layout if len(dumps["names"]) > 1 else []


@callback(
    Output(MAIN_NET_DROPDOWN, "options"),
    Output(MAIN_NET_DROPDOWN, "label"),
    Output(MAIN_NET_DROPDOWN, "value"),
    Input(DUMPS, "data"),
)
def init_main_dump_dropdown(dumps):
    if not dumps:
        return no_update, no_update, no_update

    options = [{"label": name.title(), "value": name} for name in dumps["names"]]
    return options, options[0]["label"], options[0]["value"]


@callback(
    Output(SECONDARY_NET_DROPDOWN, "options"),
    Output(SECONDARY_NET_DROPDOWN, "label"),
    Output(SECONDARY_NET_DROPDOWN, "value"),
    Input(DUMPS, "data"),
)
def init_secondary_dump_dropdown(dumps):
    if not dumps:
        return no_update, no_update, no_update

    options = [{"label": name.title(), "value": name} for name in dumps["names"]]
    return options, options[1]["label"], options[1]["value"]


@callback(
    Output(TVGT_CONF_MAT, "figure"),
    Input(MD_FILTERS, "data"),
    State(DUMPS, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    background=True,
)
def get_tvgt_conf_mat(meta_data_filters, dumps, population, main_dump, secondary_dump):
    if not population or not dumps or not main_dump or not secondary_dump:
        return no_update

    main_data = dumps["tables"]["meta_data"][main_dump]
    secondary_data = dumps["tables"]["meta_data"][secondary_dump]
    column_to_compare = "is_tv_perfect"
    query = generate_conf_mat_query(
        main_data,
        secondary_data,
        population,
        column_to_compare,
        meta_data_filters=meta_data_filters["filters_str"],
        extra_columns=meta_data_filters["md_columns"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    fig = get_confusion_matrix(data, x_label=secondary_dump, y_label=main_dump, title="TVGT Confusion Matrix")
    return fig


@callback(
    Output(GTEM_CONF_MAT, "figure"),
    Input(MD_FILTERS, "data"),
    State(DUMPS, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    background=True,
)
def get_gtem_conf_mat(meta_data_filters, dumps, population, main_dump, secondary_dump):
    if not population or not dumps or not main_dump or not secondary_dump:
        return no_update

    main_data = dumps["tables"]["meta_data"][main_dump]
    secondary_data = dumps["tables"]["meta_data"][secondary_dump]
    column_to_compare = "gtem_labels_exist"
    query = generate_conf_mat_query(
        main_data,
        secondary_data,
        population,
        column_to_compare,
        meta_data_filters=meta_data_filters["filters_str"],
        extra_columns=meta_data_filters["md_columns"],
    )
    print(query)
    data, _ = query_athena(database="run_eval_db", query=query)
    fig = get_confusion_matrix(data, x_label=secondary_dump, y_label=main_dump, title="GTEM Confusion Matrix")
    return fig


@callback(
    Output(COUNTRIES_DROPDOWN, "options"),
    Output(COUNTRIES_DROPDOWN, "label"),
    Output(COUNTRIES_DROPDOWN, "value"),
    Input(DUMPS, "data"),
)
def init_countries_dropdown(dumps):
    if not dumps:
        return no_update, no_update, no_update

    options = [{"label": name.title(), "value": name} for name in dumps["names"]]
    return options, options[0]["label"], options[0]["value"]


@callback(
    Output(COUNTRIES_HEAT_MAP, "figure"),
    Input(MD_FILTERS, "data"),
    State(DUMPS, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(COUNTRIES_DROPDOWN, "value"),
    background=True,
)
def get_countries_heat_map(meta_data_filters, dumps, population, chosen_dump):
    if not population or not dumps or not chosen_dump:
        return no_update

    md_table = dumps["tables"]["meta_data"][chosen_dump]
    group_by_column = "mdbi_country"
    query = generate_count_query(
        md_table,
        population,
        False,
        meta_data_filters=meta_data_filters["filters_str"],
        group_by_column=group_by_column,
        extra_columns=[group_by_column] + meta_data_filters["md_columns"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data["normalized"] = normalize_countries_count_to_percentiles(data["overall"].to_numpy())
    data[group_by_column] = data[group_by_column].apply(normalize_countries_names)
    data["iso_alpha"] = data[group_by_column].apply(iso_alpha_from_name)
    fig = generate_world_map(
        countries_data=data, locations="iso_alpha", color="normalized", hover_data=["overall", group_by_column]
    )
    return fig


@callback(
    Output(TVGT_PIE_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    State(DUMPS, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_tvgt_pie_chart(meta_data_filters, dumps, population, intersection_on):
    if not population or not dumps:
        return no_update

    md_tables = dumps["tables"]["meta_data"].values()
    group_by_column = "is_tv_perfect"
    query = generate_count_query(
        md_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters["filters_str"],
        group_by_column=group_by_column,
        extra_columns=[group_by_column] + meta_data_filters["md_columns"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    title = f"Distribution of TVGTs"
    fig = pie_or_line_wrapper(data, group_by_column, "overall", title=title)
    return fig


@callback(
    Output(GTEM_PIE_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    State(DUMPS, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_gtem_pie_chart(meta_data_filters, dumps, population, intersection_on):
    if not population or not dumps:
        return no_update

    md_tables = dumps["tables"]["meta_data"].values()
    group_by_column = "gtem_labels_exist"
    query = generate_count_query(
        md_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters["filters_str"],
        group_by_column=group_by_column,
        extra_columns=[group_by_column] + meta_data_filters["md_columns"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    title = f"Distribution of GTEMs"
    fig = pie_or_line_wrapper(data, group_by_column, "overall", title=title)
    return fig


@callback(
    Output(DYNAMIC_PIE_CHART_DROPDOWN, "options"),
    Input(MD_COLUMNS_OPTION, "data"),
)
def init_pie_dropdown(md_columns_options):
    if not md_columns_options:
        return no_update

    return md_columns_options


@callback(
    Output(DYNAMIC_PIE_CHART, "figure"),
    Input(DYNAMIC_PIE_CHART_DROPDOWN, "value"),
    Input(DYNAMIC_PIE_CHART_SLIDER, "value"),
    Input(MD_FILTERS, "data"),
    State(MD_COLUMNS_TO_TYPE, "data"),
    State(DUMPS, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_dynamic_pie_chart(
    group_by_column, slider_value, meta_data_filters, meta_data_dict, dumps, population, intersection_on
):
    if not population or not dumps or not group_by_column:
        return no_update

    md_tables = dumps["tables"]["meta_data"].values()
    column_type = meta_data_dict[group_by_column]
    bins_factor = None
    ignore_filter = ""
    if column_type.startswith(("int", "float", "double")):
        bin_size = exponent_transform(slider_value)
        bins_factor = bin_size
        ignore_filter = f"{group_by_column} <> 999 AND {group_by_column} <> -999"

    query = generate_count_query(
        md_tables,
        population,
        intersection_on,
        meta_data_filters=" AND ".join(
            filter_str for filter_str in [meta_data_filters["filters_str"], ignore_filter] if filter_str
        ),
        group_by_column=group_by_column,
        bins_factor=bins_factor,
        extra_columns=[group_by_column] + meta_data_filters["md_columns"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    title = f"Distribution of {group_by_column.replace('mdbi_', '').replace('_', ' ').title()}"

    if data[group_by_column].nunique() > 16:
        fig = basic_histogram_plot(data, group_by_column, "overall", title=title, color="dump_name")
    else:
        fig = pie_or_line_wrapper(data, group_by_column, "overall", title=title)
    return fig


@callback(
    Output(ROAD_TYPE_PIE_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    State(DUMPS, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_road_type_pie_chart(meta_data_filters, dumps, population, intersection_on):
    if not population or not dumps:
        return no_update

    md_tables = dumps["tables"]["meta_data"].values()
    interesting_filters = ROAD_TYPE_FILTERS
    query = generate_dynamic_count_query(
        md_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters["filters_str"],
        interesting_filters=interesting_filters["filters"],
        extra_columns=interesting_filters["extra_columns"] + meta_data_filters["md_columns"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data = data.melt(id_vars=["dump_name"], var_name="filter", value_name="overall")
    title = f"Distribution of Road Type"
    fig = pie_or_line_wrapper(data, "filter", "overall", title=title)
    return fig


@callback(
    Output(LANE_MARK_COLOR_PIE_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    State(DUMPS, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_lane_mark_color_pie_chart(meta_data_filters, dumps, population, intersection_on):
    if not population or not dumps:
        return no_update

    md_tables = dumps["tables"]["meta_data"].values()
    interesting_filters = LANE_MARK_COLOR_FILTERS
    query = generate_dynamic_count_query(
        md_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters["filters_str"],
        interesting_filters=interesting_filters["filters"],
        extra_columns=interesting_filters["extra_columns"] + meta_data_filters["md_columns"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data = data.melt(id_vars=["dump_name"], var_name="filter", value_name="overall")
    title = f"Distribution of Lane Mark Color"
    fig = pie_or_line_wrapper(data, "filter", "overall", title=title)
    return fig
