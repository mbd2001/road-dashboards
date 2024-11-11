import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, callback, dcc, html, no_update
from pypika import Criterion, EmptyCriterion, Query, functions
from pypika.terms import Term

from road_dashboards.road_dump_dashboard.graphical_components.histogram_plot import basic_histogram_plot
from road_dashboards.road_dump_dashboard.graphical_components.line_graph import draw_line_graph
from road_dashboards.road_dump_dashboard.graphical_components.pie_chart import basic_pie_chart
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import (
    base_data_subquery,
    percentage_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import Round, execute, load_object
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class CountGraph(GridObject):
    """
    Defines the properties of count graph

    Attributes:
            columns (list[Selectable]): columns to group by (and count)
            slider_value (int): optional. round after n decimal places, default None
            filter (str): optional. filter to apply on the datasets
    """

    def __init__(
        self,
        column: Term,
        title: str,
        main_table: str,
        page_filters_id: str,
        intersection_switch_id: str,
        filter: Criterion = EmptyCriterion(),
        slider_value: int | None = None,
        full_grid_row: bool = False,
        component_id: str = "",
    ):
        self.column = column
        self.title = title
        self.main_table = main_table
        self.page_filters_id = page_filters_id
        self.intersection_switch_id = intersection_switch_id
        self.filter = filter
        self.slider_value = slider_value
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.count_chart_id = self._generate_id("count_chart")
        self.filter_ignores_switch_id = self._generate_id("filter_ignores_switch")
        self.percentage_switch_id = self._generate_id("percentage_switch")
        self.bins_slider = self._generate_id("bins_slider")

    def layout(self):
        graph = loading_wrapper(
            dcc.Graph(
                id=self.count_chart_id,
                config={"displayModeBar": False},
            )
        )
        percentage_button = daq.BooleanSwitch(
            id=self.percentage_switch_id,
            on=False,
            label="Absolute <-> Percentage",
            labelPosition="top",
        )
        slider = dcc.Slider(
            -2,
            3,
            1,
            id=self.bins_slider,
            vertical=True,
            marks={i: "{}".format(i) for i in range(-2, 4)},
            value=self.slider_value,
        )

        filter_ignores_button = daq.BooleanSwitch(
            id=self.filter_ignores_switch_id,
            on=True,
            label="Show All <-> Filter Ignores",
            labelPosition="top",
        )

        if self.slider_value is not None:
            graph_row = dbc.Row([dbc.Col(graph, width=11), dbc.Col(slider, width=1)])
        else:
            graph_row = dbc.Row([graph, html.Div(slider, hidden=True)])

        if not isinstance(self.filter, EmptyCriterion):
            buttons_row = dbc.Row([dbc.Col(percentage_button), dbc.Col(filter_ignores_button)])
        else:
            buttons_row = dbc.Row([dbc.Col([percentage_button, html.Div(filter_ignores_button, hidden=True)])])

        group_by_layout = card_wrapper([graph_row, buttons_row])
        return group_by_layout

    def _callbacks(self):
        @callback(
            Output(self.count_chart_id, "figure"),
            Input(self.bins_slider, "value"),
            Input(self.percentage_switch_id, "on"),
            Input(self.filter_ignores_switch_id, "on"),
            Input(self.main_table, "data"),
            Input(META_DATA, "data"),
            Input(self.intersection_switch_id, "on"),
            Input(self.page_filters_id, "data"),
        )
        def get_count_chart(
            round_n_decimal_place,
            compute_percentage,
            filter_ignores,
            main_tables,
            md_tables,
            intersection_on,
            page_filters,
        ):
            if not main_tables:
                return no_update

            main_tables: list[Base] = load_object(main_tables)
            md_tables: list[Base] = load_object(md_tables) if md_tables else None
            page_filters: Criterion = load_object(page_filters)

            dump_name = MetaData.dump_name
            base = base_data_subquery(
                main_tables=main_tables,
                terms=[round_term(self.column, round_n_decimal_place), dump_name],
                meta_data_tables=md_tables,
                data_filter=self.filter if filter_ignores else EmptyCriterion(),
                page_filters=page_filters,
                intersection_on=intersection_on,
            )
            query = (
                Query.from_(base)
                .groupby(self.column.alias, dump_name)
                .select(self.column.alias, dump_name, functions.Count("*", "overall"))
            )
            if compute_percentage:
                query = percentage_wrapper(query, query.overall, [dump_name], [self.column])

            y_col = "percentage" if compute_percentage else "overall"
            data = execute(query.orderby(dump_name))
            fig = pie_or_line_graph(data, self.column.alias, y_col, title=self.title, color=dump_name.alias)
            return fig


def pie_or_line_graph(data, names, values, title="", hover=None, color="dump_name"):
    if data[names].nunique() > 16:
        fig = basic_histogram_plot(data, names, values, title=title)
    elif data[color].nunique() == 1:
        fig = basic_pie_chart(data, names, values, title=title, hover=hover)
    else:
        fig = draw_line_graph(data, names, values, title=title, hover=hover, color=color)

    return fig


def round_term(column: Term, round_n_decimal_place: int = None):
    return (
        Round(column, round_n_decimal_place, alias=column.alias)
        if isinstance(column, Column) and column.type in [int, float] and round_n_decimal_place is not None
        else column
    )
