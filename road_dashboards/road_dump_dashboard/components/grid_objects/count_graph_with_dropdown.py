from dataclasses import dataclass

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, callback, dcc, html, no_update

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import Column
from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    DYNAMIC_CHART,
    DYNAMIC_CHART_DROPDOWN,
    DYNAMIC_CHART_SLIDER,
    DYNAMIC_PERCENTAGE_SWITCH,
    INTERSECTION_SWITCH,
    MAIN_TABLES,
    MD_TABLES,
    PAGE_FILTERS,
)
from road_dashboards.road_dump_dashboard.components.constants.queries_properties import BaseDataQuery, GroupByQuery
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.components.grid_objects.count_graph import pie_or_line_graph
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    TableType,
    get_columns_dict,
    get_existing_column,
    load_object,
)
from road_dashboards.road_dump_dashboard.graphs.histogram_plot import basic_histogram_plot


@dataclass
class GroupByGraphWithDropdown(GridObject):
    """
    Defines the properties of group by graph
    """

    title: str = DYNAMIC_CHART
    full_grid: bool = True
    slider_value: int = 2

    def layout(self):
        graph = loading_wrapper(
            dcc.Graph(
                id=self.title,
                config={"displayModeBar": False},
            )
        )
        percentage_button = daq.BooleanSwitch(
            id=DYNAMIC_PERCENTAGE_SWITCH,
            on=False,
            label="Absolute <-> Percentage",
            labelPosition="top",
        )
        slider = dcc.Slider(
            -2,
            3,
            1,
            id=DYNAMIC_CHART_SLIDER,
            vertical=True,
            marks={i: "{}".format(i) for i in range(-2, 4)},
            value=self.slider_value,
        )
        graph_row = dbc.Row([dbc.Col(graph, width=11), dbc.Col(slider, width=1)])
        buttons_row = dbc.Row(percentage_button)
        dynamic_chart = html.Div(
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
                dbc.Row(html.Div([graph_row, buttons_row])),
            ]
        )
        return dynamic_chart


@callback(Output(DYNAMIC_CHART_DROPDOWN, "options"), Input(MAIN_TABLES, "data"))
def init_dynamic_chart_dropdown(main_tables):
    if not main_tables:
        return no_update

    main_tables: TableType = load_object(main_tables)
    columns_options = get_columns_dict(main_tables)
    return columns_options


@callback(
    Output(DYNAMIC_CHART, "figure"),
    Input(DYNAMIC_CHART_DROPDOWN, "value"),
    Input(DYNAMIC_CHART_SLIDER, "value"),
    Input(DYNAMIC_PERCENTAGE_SWITCH, "on"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
    Input(INTERSECTION_SWITCH, "on"),
    Input(PAGE_FILTERS, "data"),
)
def get_dynamic_chart(
    column,
    round_n_decimal_place,
    compute_percentage,
    main_tables,
    md_tables,
    intersection_on,
    page_filters,
):
    if not main_tables or not column:
        return no_update

    if getattr(column, "round_n_decimal_place", False) is not False:
        column.round_n_decimal_place = round_n_decimal_place

    main_tables: TableType = load_object(main_tables)
    md_tables: TableType = load_object(md_tables) if md_tables else None
    column = get_existing_column(column, main_tables, md_tables)
    query = GroupByQuery(
        group_by_columns=[column],
        compute_percentage=compute_percentage,
        sub_query=BaseDataQuery(
            main_tables=main_tables.tables,
            meta_data_tables=md_tables.tables if md_tables else None,
            page_filters=page_filters,
            intersection_on=intersection_on,
            extra_columns=[column],
        ),
    )
    data = query.get_results()
    y_col = "percentage" if compute_percentage else "overall"
    if data[column.name].nunique() > 16:
        fig = basic_histogram_plot(data, column.name, y_col, title=f"{column.name.title()} Distribution")
    else:
        fig = pie_or_line_graph(data, column.name, y_col, title=f"{column.name.title()} Distribution")

    return fig
