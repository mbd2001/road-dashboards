import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dcc, html, no_update, register_page
from road_database_toolkit.athena.athena_utils import query_athena

from road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_eval_dashboard.components.common_filters import LANE_MARK_COLOR_FILTERS, ROAD_TYPE_FILTERS
from road_eval_dashboard.components.components_ids import (
    COUNTRIES_HEAT_MAP,
    DYNAMIC_PIE_CHART,
    DYNAMIC_PIE_CHART_DROPDOWN,
    DYNAMIC_PIE_CHART_SLIDER,
    GTEM_PIE_CHART,
    LANE_MARK_COLOR_PIE_CHART,
    MD_COLUMNS_OPTION,
    MD_COLUMNS_TO_TYPE,
    MD_FILTERS,
    NETS,
    ROAD_TYPE_PIE_CHART,
    TVGT_PIE_CHART,
)
from road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.components.queries_manager import generate_count_query, generate_dynamic_count_query
from road_eval_dashboard.graphs.countries_map import (
    generate_world_map,
    iso_alpha_from_name,
    normalize_countries_count_to_percentiles,
    normalize_countries_names,
)
from road_eval_dashboard.graphs.histogram_plot import basic_histogram_plot
from road_eval_dashboard.graphs.pie_chart import basic_pie_chart

extra_properties = PageProperties("search")
register_page(__name__, path="/data_exploration", name="Data Exploration", order=1, **extra_properties.__dict__)


def exponent_transform(value, base=10):
    return base**value


layout = html.Div(
    [
        html.H1("Data Exploration", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.gt_layout,
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
                            graph_wrapper(DYNAMIC_PIE_CHART),
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
                    card_wrapper([graph_wrapper(TVGT_PIE_CHART)]),
                    width=6,
                ),
                dbc.Col(
                    card_wrapper([graph_wrapper(GTEM_PIE_CHART)]),
                    width=6,
                ),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    card_wrapper([graph_wrapper(ROAD_TYPE_PIE_CHART)]),
                    width=6,
                ),
                dbc.Col(
                    card_wrapper([graph_wrapper(LANE_MARK_COLOR_PIE_CHART)]),
                    width=6,
                ),
            ],
        ),
        card_wrapper([dbc.Row(graph_wrapper(COUNTRIES_HEAT_MAP))]),
    ]
)


@callback(
    Output(COUNTRIES_HEAT_MAP, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    background=True,
)
def get_countries_heat_map(meta_data_filters, nets):
    if not nets:
        return no_update

    group_by_column = "mdbi_country"
    query = generate_count_query(
        nets["frame_tables"], nets["meta_data"], meta_data_filters=meta_data_filters, group_by_column=group_by_column
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data["overall"] = data["overall"] / len(nets["names"])
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
    Input(NETS, "data"),
    background=True,
)
def get_tvgt_pie_chart(meta_data_filters, nets):
    if not nets:
        return no_update

    group_by_column = "is_tv_perfect"
    query = generate_count_query(
        nets["frame_tables"], nets["meta_data"], meta_data_filters=meta_data_filters, group_by_column=group_by_column
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data["overall"] = data["overall"] / len(nets["names"])
    title = f"Distribution of TVGTs"
    fig = basic_pie_chart(data, group_by_column, "overall", title=title)
    return fig


@callback(
    Output(GTEM_PIE_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    background=True,
)
def get_gtem_pie_chart(meta_data_filters, nets):
    if not nets:
        return no_update

    group_by_column = "gtem_labels_exist"
    query = generate_count_query(
        nets["frame_tables"], nets["meta_data"], meta_data_filters=meta_data_filters, group_by_column=group_by_column
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data["overall"] = data["overall"] / len(nets["names"])
    title = f"Distribution of GTEMs"
    fig = basic_pie_chart(data, group_by_column, "overall", title=title)
    return fig


@callback(
    Output(DYNAMIC_PIE_CHART_DROPDOWN, "options"),
    Input(MD_COLUMNS_OPTION, "data"),
)
def init_pie_dropdown(md_columns_options):
    return md_columns_options or []


@callback(
    Output(DYNAMIC_PIE_CHART, "figure"),
    Input(DYNAMIC_PIE_CHART_DROPDOWN, "value"),
    Input(DYNAMIC_PIE_CHART_SLIDER, "value"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    State(MD_COLUMNS_TO_TYPE, "data"),
    background=True,
)
def get_dynamic_pie_chart(group_by_column, slider_value, meta_data_filters, nets, meta_data_dict):
    if not nets or not group_by_column:
        return no_update

    column_type = meta_data_dict[group_by_column]
    bins_factor = None
    ignore_filter = ""
    if column_type.startswith(("int", "float", "double")):
        bin_size = exponent_transform(slider_value)
        bins_factor = bin_size
        ignore_filter = f"{group_by_column} <> 999 AND {group_by_column} <> -999"

    query = generate_count_query(
        nets["frame_tables"],
        nets["meta_data"],
        meta_data_filters=" AND ".join(filter_str for filter_str in [meta_data_filters, ignore_filter] if filter_str),
        group_by_column=group_by_column,
        bins_factor=bins_factor,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data["overall"] = data["overall"] / len(nets["names"])
    title = f"Distribution of {group_by_column.replace('mdbi_', '').replace('_', ' ').title()}"

    if len(data.index) > 16:
        fig = basic_histogram_plot(data, group_by_column, "overall", title=title)
    else:
        fig = basic_pie_chart(data, group_by_column, "overall", title=title)
    return fig


@callback(
    Output(ROAD_TYPE_PIE_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    background=True,
)
def get_road_type_pie_chart(meta_data_filters, nets):
    if not nets:
        return no_update

    interesting_filters = ROAD_TYPE_FILTERS
    query = generate_dynamic_count_query(
        nets["frame_tables"],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        interesting_filters=interesting_filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data = data.drop("net_id", axis=1).iloc[0]
    data = pd.DataFrame({"filters": data.index.map(lambda x: x.replace("overall_", "")), "overall": data})
    title = f"Distribution of Road Type"
    fig = basic_pie_chart(data, list(interesting_filters.keys()), "overall", title=title)
    return fig


@callback(
    Output(LANE_MARK_COLOR_PIE_CHART, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    background=True,
)
def get_lane_mark_color_pie_chart(meta_data_filters, nets):
    if not nets:
        return no_update

    interesting_filters = LANE_MARK_COLOR_FILTERS
    query = generate_dynamic_count_query(
        nets["frame_tables"],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        interesting_filters=interesting_filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data = data.drop("net_id", axis=1).iloc[0]
    data = pd.DataFrame({"filters": data.index.map(lambda x: x.replace("overall_", "")), "overall": data})
    title = f"Distribution of Lane Mark Color"
    fig = basic_pie_chart(data, list(interesting_filters.keys()), "overall", title=title)
    return fig
