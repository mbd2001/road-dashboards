import itertools
from dataclasses import dataclass
from typing import List

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, callback, dcc, html, no_update

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import Case, NumericColumn
from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    GENERIC_CASES_CHART,
    GENERIC_COUNT_EXTRA_INFO,
    GENERIC_FILTER_IGNORES_SWITCH,
    GENERIC_PERCENTAGE_SWITCH,
    INTERSECTION_SWITCH,
    MAIN_TABLES,
    MD_TABLES,
    PAGE_FILTERS,
)
from road_dashboards.road_dump_dashboard.components.constants.queries_properties import (
    BaseDataQuery,
    CasesQuery,
    GroupByQuery,
)
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import loading_wrapper
from road_dashboards.road_dump_dashboard.components.grid_objects.count_graph import pie_or_line_graph
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    Table,
    TableType,
    dump_object,
    load_object,
)
from road_dashboards.road_dump_dashboard.graphs.histogram_plot import basic_histogram_plot


@dataclass
class CasesGraph(GridObject):
    """
    Defines the properties of group by graph

    Attributes:
            include_slider (bool): optional. True if the graph should include slider
            slider_default_value (int): optional. default value for the slider
    """

    cases: List[Case]
    filter: str = None

    def layout(self):
        graph = loading_wrapper(
            dcc.Graph(
                id={
                    "type": GENERIC_CASES_CHART,
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
        filter_ignores_button = daq.BooleanSwitch(
            id={"type": GENERIC_FILTER_IGNORES_SWITCH, "index": self.title},
            on=True,
            label="Show All <-> Filter Ignores",
            labelPosition="top",
        )
        if self.filter:
            buttons_row = dbc.Row([dbc.Col(percentage_button), dbc.Col(filter_ignores_button)])
        else:
            buttons_row = dbc.Row([dbc.Col([percentage_button, html.Div(filter_ignores_button, hidden=True)])])

        graph_row = dbc.Row([graph])
        extra_info = html.Div(
            id={"type": GENERIC_COUNT_EXTRA_INFO, "index": self.title},
            hidden=True,
            **{"data-graph": dump_object(self)},
        )
        group_by_layout = html.Div([graph_row, buttons_row, extra_info])
        return group_by_layout


@callback(
    Output({"type": GENERIC_CASES_CHART, "index": MATCH}, "figure"),
    Input({"type": GENERIC_PERCENTAGE_SWITCH, "index": MATCH}, "on"),
    Input({"type": GENERIC_FILTER_IGNORES_SWITCH, "index": MATCH}, "on"),
    Input({"type": GENERIC_COUNT_EXTRA_INFO, "index": MATCH}, "data-graph"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
    Input(INTERSECTION_SWITCH, "on"),
    Input(PAGE_FILTERS, "data"),
)
def get_cases_chart(
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
    properties: CasesGraph = load_object(properties)
    cases = properties.cases
    cases_columns = list(itertools.chain(*[case.extra_columns for case in cases]))

    query = GroupByQuery(
        group_by_columns=[NumericColumn("cases")],
        sub_query=CasesQuery(
            interesting_cases=cases,
            sub_query=BaseDataQuery(
                main_tables=main_tables,
                meta_data_tables=md_tables,
                data_filter=properties.filter if filter_ignores else None,
                page_filters=page_filters,
                intersection_on=intersection_on,
                extra_columns=cases_columns,
            ),
        ),
        compute_percentage=compute_percentage,
    )
    data = query.get_results()
    y_col = "percentage" if compute_percentage else "overall"
    if data["cases"].nunique() > 16:
        fig = basic_histogram_plot(data, "cases", y_col, title=properties.title)
    else:
        fig = pie_or_line_graph(data, "cases", y_col, title=properties.title)

    return fig
