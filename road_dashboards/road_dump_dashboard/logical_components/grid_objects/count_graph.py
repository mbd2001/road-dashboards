import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, State, callback, dcc, html, no_update
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
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import (
    Round,
    execute,
    load_object,
    optional_inputs,
)
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
        main_table: str,
        title: str = "",
        page_filters_id: str = "",
        intersection_switch_id: str = "",
        column: Term | None = None,
        columns_dropdown_id: str = "",
        filter: Criterion = EmptyCriterion(),
        slider_value: int | None = None,
        full_grid_row: bool = False,
        component_id: str = "",
    ):
        self.title = title
        self.main_table = main_table
        self.page_filters_id = page_filters_id
        self.intersection_switch_id = intersection_switch_id
        self.column = column
        self.columns_dropdown_id = columns_dropdown_id
        self.filter = filter
        self.slider_value = slider_value
        assert (
            self.column or self.columns_dropdown_id
        ), "you have to provide input column, explicitly or through dropdown"
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
            buttons_row = dbc.Row([percentage_button, html.Div(filter_ignores_button, hidden=True)])

        group_by_layout = card_wrapper([graph_row, buttons_row])
        return group_by_layout

    def _callbacks(self):
        @callback(
            Output(self.count_chart_id, "figure"),
            Input(self.main_table, "data"),
            State(META_DATA, "data"),
            Input(self.percentage_switch_id, "on"),
            Input(self.bins_slider, "value"),
            Input(self.filter_ignores_switch_id, "on"),
            optional_inputs(
                intersection_on=Input(self.intersection_switch_id, "on"),
                page_filters=Input(self.page_filters_id, "data"),
                column=Input(self.columns_dropdown_id, "value"),
            ),
        )
        def get_count_chart(
            main_tables,
            md_tables,
            compute_percentage,
            round_n_decimal_place,
            filter_ignores,
            optional,
        ):
            if not main_tables:
                return no_update

            main_tables: list[Base] = load_object(main_tables)
            column: Term = self.column or getattr(type(main_tables[0]), optional["column"], None)
            if not column:
                return no_update

            md_tables: list[Base] = load_object(md_tables)
            intersection_on: bool = optional.get("intersection_on", False)
            page_filters: str = optional.get("page_filters", None)
            page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()

            dump_name = MetaData.dump_name
            base = base_data_subquery(
                main_tables=main_tables,
                meta_data_tables=md_tables,
                terms=[self.round_term(column, round_n_decimal_place), dump_name],
                data_filter=self.filter if filter_ignores else EmptyCriterion(),
                page_filters=page_filters,
                intersection_on=intersection_on,
            )
            query = (
                Query.from_(base)
                .groupby(column.alias, dump_name)
                .select(column.alias, dump_name, functions.Count("*", "overall"))
            )
            if compute_percentage:
                query = percentage_wrapper(query, query.overall, [dump_name], [column])

            y_col = "percentage" if compute_percentage else "overall"
            data = execute(query)
            title = self.title or f"{column.alias.title()} Distribution"
            fig = self.pie_or_line_graph(data, column.alias, y_col, title=title, color=dump_name.alias)
            return fig

    @staticmethod
    def pie_or_line_graph(data, names, values, title="", hover=None, color="dump_name"):
        if data[names].nunique() > 16:
            fig = basic_histogram_plot(data, names, values, title=title)
        elif data[color].nunique() == 1:
            fig = basic_pie_chart(data, names, values, title=title, hover=hover)
        else:
            fig = draw_line_graph(data, names, values, title=title, hover=hover, color=color)

        return fig

    @staticmethod
    def round_term(column: Term, round_n_decimal_place: int | None = None):
        return (
            Round(column, round_n_decimal_place, alias=column.alias)
            if isinstance(column, Column) and column.type in [int, float] and round_n_decimal_place is not None
            else column
        )
