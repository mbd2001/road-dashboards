import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, State, callback, dcc, html, no_update
from pypika import Criterion, Query, functions

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.init_data_sources import EXISTING_TABLES
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import (
    base_data_subquery,
    percentage_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.count_graph import (
    pie_or_line_graph,
    round_term,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import execute, load_object
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class CountGraphWithDropdown(GridObject):
    """
    Defines the properties of group by graph

    Attributes:
        slider_value (int): optional. round after n decimal places, default 2
    """

    def __init__(
        self,
        main_table: str,
        page_filters_id: str,
        intersection_switch_id: str,
        slider_value: int = 1,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.main_table = main_table
        self.page_filters_id = page_filters_id
        self.intersection_switch_id = intersection_switch_id
        self.slider_value = slider_value
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.count_chart_id = self._generate_id("count_chart")
        self.columns_dropdown_id = self._generate_id("columns_dropdown")
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
        graph_row = dbc.Row([dbc.Col(graph, width=11), dbc.Col(slider, width=1)])
        buttons_row = dbc.Row(percentage_button)
        dynamic_chart = card_wrapper(
            [
                dbc.Row(
                    dcc.Dropdown(
                        id=self.columns_dropdown_id,
                        multi=False,
                        placeholder="Attribute",
                        options=EXISTING_TABLES[self.main_table].get_columns(),
                        value=None,
                    )
                ),
                dbc.Row(html.Div([graph_row, buttons_row])),
            ]
        )
        return dynamic_chart

    def _callbacks(self):
        @callback(
            Output(self.count_chart_id, "figure"),
            Input(self.columns_dropdown_id, "value"),
            Input(self.bins_slider, "value"),
            Input(self.percentage_switch_id, "on"),
            Input(self.main_table, "data"),
            State(META_DATA, "data"),
            Input(self.intersection_switch_id, "on"),
            Input(self.page_filters_id, "data"),
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

            main_tables: list[Base] = load_object(main_tables)
            md_tables: list[Base] = load_object(md_tables) if md_tables else None
            column: Column = getattr(EXISTING_TABLES[self.main_table], column, None)
            page_filters: Criterion = load_object(page_filters)

            dump_name = MetaData.dump_name
            columns = [round_term(column, round_n_decimal_place=round_n_decimal_place), dump_name]
            base = base_data_subquery(
                main_tables=main_tables,
                meta_data_tables=md_tables,
                terms=columns,
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

            data = execute(query)
            y_col = "percentage" if compute_percentage else "overall"
            fig = pie_or_line_graph(
                data, column.alias, y_col, title=f"{column.alias.title()} Distribution", color="dump_name"
            )
            return fig
