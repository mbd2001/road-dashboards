from dataclasses import dataclass
from typing import List

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import Column
from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    GENERIC_CONF_EXTRA_INFO,
    GENERIC_CONF_MAT,
    GENERIC_FILTER_IGNORES_BTN,
    GENERIC_SHOW_DIFF_BTN,
    MAIN_NET_DROPDOWN,
    MAIN_TABLES,
    MD_TABLES,
    PAGE_FILTERS,
    SECONDARY_NET_DROPDOWN,
)
from road_dashboards.road_dump_dashboard.components.constants.queries_properties import BaseDataQuery, ConfMatQuery
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import loading_wrapper
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    Table,
    dump_object,
    load_object,
)
from road_dashboards.road_dump_dashboard.graphs.confusion_matrix import get_confusion_matrix


@dataclass
class ConfMatGraph(GridObject):
    """
    Defines the properties of group by graph

    Attributes:
            include_ignore_btn (bool):
    """

    column: Column
    filter: str = None

    def layout(self):
        mat_row = dbc.Row(
            loading_wrapper(
                dcc.Graph(
                    id={"type": GENERIC_CONF_MAT, "index": self.title},
                    config={"displayModeBar": False},
                )
            )
        )
        draw_diff_button = dbc.Button(
            "Draw Diff Frames",
            id={"type": GENERIC_SHOW_DIFF_BTN, "index": self.title},
            className="bg-primary mt-5",
        )
        filter_ignores_button = daq.BooleanSwitch(
            id={"type": GENERIC_FILTER_IGNORES_BTN, "index": self.title},
            on=False,
            label="Show All <-> Filter Ignores",
            labelPosition="top",
        )

        if self.filter:
            buttons_row = dbc.Row([dbc.Col(draw_diff_button), dbc.Col(filter_ignores_button)])
        else:
            buttons_row = dbc.Row([dbc.Col([draw_diff_button, html.Div(filter_ignores_button, hidden=True)])])

        extra_info = html.Div(
            id={"type": GENERIC_CONF_EXTRA_INFO, "index": self.title},
            hidden=True,
            **{"data-graph": dump_object(self)},
        )
        single_mat_layout = html.Div([mat_row, buttons_row, extra_info])
        return single_mat_layout


@callback(
    Output({"type": GENERIC_CONF_MAT, "index": MATCH}, "figure"),
    Input(PAGE_FILTERS, "data"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    State({"type": GENERIC_CONF_EXTRA_INFO, "index": MATCH}, "data-graph"),
    Input({"type": GENERIC_FILTER_IGNORES_BTN, "index": MATCH}, "on"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
)
def get_conf_mat(page_filters, main_dump, secondary_dump, properties, filter_ignores, main_tables, md_tables):
    if not main_tables or not main_dump or not secondary_dump:
        return no_update

    main_tables: List[Table] = load_object(main_tables).tables
    md_tables: List[Table] = load_object(md_tables).tables if md_tables else None
    properties: ConfMatGraph = load_object(properties)
    column = properties.column
    if getattr(column, "filter", False) is not False and filter_ignores is False:
        column.filter = None

    query = ConfMatQuery(
        column_to_compare=column,
        main_data_query=BaseDataQuery(
            main_tables=main_tables,
            meta_data_tables=md_tables,
            data_filter=properties.filter if filter_ignores else None,
            page_filters=page_filters,
            dumps_to_include=[main_dump],
            extra_columns=[column],
        ),
        secondary_data_query=BaseDataQuery(
            main_tables=main_tables,
            meta_data_tables=md_tables,
            data_filter=properties.filter if filter_ignores else None,
            page_filters=page_filters,
            dumps_to_include=[secondary_dump],
            extra_columns=[column],
        ),
    )
    data = query.get_results()
    fig = get_confusion_matrix(data, x_label=secondary_dump, y_label=main_dump, title=properties.title)
    return fig
