from dataclasses import dataclass
from typing import List

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, callback, dcc, html, no_update

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import Column
from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    GENERIC_BINS_SLIDER,
    GENERIC_COUNT_CHART,
    GENERIC_COUNT_EXTRA_INFO,
    GENERIC_FILTER_IGNORES_SWITCH,
    GENERIC_PERCENTAGE_SWITCH,
    INTERSECTION_SWITCH,
    MAIN_TABLES,
    MD_TABLES,
    PAGE_FILTERS,
)
from road_dashboards.road_dump_dashboard.components.constants.queries_properties import BaseDataQuery, GroupByQuery
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import loading_wrapper
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    Table,
    TableType,
    dump_object,
    load_object,
)
from road_dashboards.road_dump_dashboard.graphs.histogram_plot import basic_histogram_plot
from road_dashboards.road_dump_dashboard.graphs.line_graph import draw_line_graph
from road_dashboards.road_dump_dashboard.graphs.pie_chart import basic_pie_chart


@dataclass
class GroupByGraph(GridObject):
    """
    Defines the properties of group by graph

    Attributes:
            slider_value (int): optional. init value for the slider
    """

    columns: List[Column]
    slider_value: int = None
    filter: str = None

    def layout(self):
        graph = loading_wrapper(
            dcc.Graph(
                id={
                    "type": GENERIC_COUNT_CHART,
                    "index": self.title,
                },
                config={"displayModeBar": False},
            )
        )
        percentage_button = daq.BooleanSwitch(
            id={"type": GENERIC_PERCENTAGE_SWITCH, "index": self.title},
            on=False,
            label="Absolute <-> Percentage",
            labelPosition="top",
        )
        slider = dcc.Slider(
            -2,
            3,
            1,
            id={"type": GENERIC_BINS_SLIDER, "index": self.title},
            vertical=True,
            marks={i: "{}".format(i) for i in range(-2, 4)},
            value=self.slider_value,
        )

        filter_ignores_button = daq.BooleanSwitch(
            id={"type": GENERIC_FILTER_IGNORES_SWITCH, "index": self.title},
            on=True,
            label="Show All <-> Filter Ignores",
            labelPosition="top",
        )

        if self.slider_value is not None:
            graph_row = dbc.Row([dbc.Col(graph, width=11), dbc.Col(slider, width=1)])
        else:
            graph_row = dbc.Row([graph, html.Div(slider, hidden=True)])

        if self.filter:
            buttons_row = dbc.Row([dbc.Col(percentage_button), dbc.Col(filter_ignores_button)])
        else:
            buttons_row = dbc.Row([dbc.Col([percentage_button, html.Div(filter_ignores_button, hidden=True)])])

        extra_info = html.Div(
            id={"type": GENERIC_COUNT_EXTRA_INFO, "index": self.title},
            hidden=True,
            **{"data-graph": dump_object(self)},
        )
        group_by_layout = html.Div([graph_row, buttons_row, extra_info])
        return group_by_layout


@callback(
    Output({"type": GENERIC_COUNT_CHART, "index": MATCH}, "figure"),
    Input({"type": GENERIC_BINS_SLIDER, "index": MATCH}, "value"),
    Input({"type": GENERIC_PERCENTAGE_SWITCH, "index": MATCH}, "on"),
    Input({"type": GENERIC_FILTER_IGNORES_SWITCH, "index": MATCH}, "on"),
    Input({"type": GENERIC_COUNT_EXTRA_INFO, "index": MATCH}, "data-graph"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
    Input(INTERSECTION_SWITCH, "on"),
    Input(PAGE_FILTERS, "data"),
)
def get_count_chart(
    round_n_decimal_place,
    compute_percentage,
    filter_ignores,
    properties,
    main_tables,
    md_tables,
    intersection_on,
    page_filters,
):
    if not main_tables:
        return no_update

    main_tables: List[Table] = load_object(main_tables).tables
    md_tables: List[Table] = load_object(md_tables).tables if md_tables else None
    properties: GroupByGraph = load_object(properties)
    columns = properties.columns
    fix_columns_according_to_callback_state(columns, round_n_decimal_place, filter_ignores)

    query = GroupByQuery(
        group_by_columns=columns,
        compute_percentage=compute_percentage,
        sub_query=BaseDataQuery(
            main_tables=main_tables,
            meta_data_tables=md_tables,
            data_filter=properties.filter if filter_ignores else None,
            page_filters=page_filters,
            intersection_on=intersection_on,
            extra_columns=columns,
        ),
    )
    data = query.get_results()
    y_col = "percentage" if compute_percentage else "overall"
    if data[columns[0].name].nunique() > 16:
        fig = basic_histogram_plot(data, columns[0].name, y_col, title=properties.title)
    else:
        fig = pie_or_line_graph(data, columns[0].name, y_col, title=properties.title)

    return fig


def fix_columns_according_to_callback_state(
    columns: List[Column], round_n_decimal_place: int = None, filter_ignores: bool = False
):
    for column in columns:
        if getattr(column, "round_n_decimal_place", False) is not False:
            column.round_n_decimal_place = round_n_decimal_place
        if getattr(column, "filter", False) is not False and filter_ignores is False:
            column.filter = None


def pie_or_line_graph(data, names, values, title="", hover=None, color="dump_name"):
    if data[color].nunique() == 1:
        fig = basic_pie_chart(data, names, values, title=title, hover=hover)
    else:
        fig = draw_line_graph(data, names, values, title=title, hover=hover, color=color)

    return fig
