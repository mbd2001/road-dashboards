from dataclasses import dataclass
from typing import List

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, callback, html, no_update

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import NumericColumn, StringColumn
from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    INTERSECTION_SWITCH,
    MAIN_TABLES,
    MD_TABLES,
    OBJ_COUNT_CHART,
    OBJ_COUNT_PERCENTAGE_SWITCH,
    PAGE_FILTERS,
)
from road_dashboards.road_dump_dashboard.components.constants.queries_properties import (
    BaseDataQuery,
    CountMetric,
    GroupByQuery,
)
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    Table,
    TableType,
    load_object,
)
from road_dashboards.road_dump_dashboard.graphs.histogram_plot import basic_histogram_plot


@dataclass
class ObjCountGraph(GridObject):
    """
    Defines the properties of group by graph

    Attributes:
            include_slider (bool): optional. True if the graph should include slider
            slider_default_value (int): optional. default value for the slider
    """

    title: str = OBJ_COUNT_CHART
    full_grid_row: bool = True

    def layout(self):
        graph_row = super().layout()
        percentage_button = daq.BooleanSwitch(
            id=OBJ_COUNT_PERCENTAGE_SWITCH,
            on=False,
            label="Absolute <-> Percentage",
            labelPosition="top",
        )

        buttons_row = dbc.Row([dbc.Col(percentage_button)])
        group_by_layout = html.Div([graph_row, buttons_row])
        return group_by_layout


@callback(
    Output(OBJ_COUNT_CHART, "figure"),
    Input(OBJ_COUNT_PERCENTAGE_SWITCH, "on"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
    Input(INTERSECTION_SWITCH, "on"),
    Input(PAGE_FILTERS, "data"),
)
def get_dynamic_chart(
    compute_percentage,
    main_tables,
    md_tables,
    intersection_on,
    page_filters,
):
    if not main_tables:
        return no_update

    main_tables: List[Table] = load_object(main_tables).tables
    md_tables: List[Table] = load_object(md_tables).tables if md_tables else None
    query = GroupByQuery(
        group_by_columns=[NumericColumn("objects_per_frame")],
        sub_query=GroupByQuery(
            group_by_columns=[StringColumn("clip_name"), NumericColumn("grabindex")],
            sub_query=BaseDataQuery(
                main_tables=main_tables,
                meta_data_tables=md_tables,
                page_filters=page_filters,
                intersection_on=intersection_on,
            ),
            metric=CountMetric(output_name="objects_per_frame"),
        ),
        compute_percentage=compute_percentage,
    )
    data = query.get_results()
    y_col = "percentage" if compute_percentage else "overall"
    fig = basic_histogram_plot(data, "objects_per_frame", y_col, title="Objects Count")
    return fig
