import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, State, callback, dcc, no_update
from pypika import Criterion, EmptyCriterion, functions
from pypika.queries import Query

from road_dashboards.road_dump_dashboard.graphical_components.histogram_plot import basic_histogram_plot
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import base_data_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.count_graph import CountGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import execute, load_object, optional_inputs
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class ObjCountGraph(GridObject):
    """
    Defines the properties of objects count graph
    """

    def __init__(
        self,
        main_table: str,
        intersection_switch_id: str = "",
        page_filters_id: str = "",
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.main_table = main_table
        self.page_filters_id = page_filters_id
        self.intersection_switch_id = intersection_switch_id
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.obj_count_id = self._generate_id("obj_count")
        self.percentage_switch_id = self._generate_id("percentage_switch")

    def layout(self):
        graph_row = dbc.Row(
            loading_wrapper(
                dcc.Graph(
                    id=self.obj_count_id,
                    config={"displayModeBar": False},
                )
            )
        )
        percentage_button = daq.BooleanSwitch(
            id=self.percentage_switch_id,
            on=False,
            label="Absolute <-> Percentage",
            labelPosition="top",
        )

        buttons_row = dbc.Row([dbc.Col(percentage_button)])
        group_by_layout = card_wrapper([graph_row, buttons_row])
        return group_by_layout

    def _callbacks(self):
        @callback(
            Output(self.obj_count_id, "figure"),
            Input(self.percentage_switch_id, "on"),
            Input(self.main_table, "data"),
            State(META_DATA, "data"),
            optional_inputs(
                intersection_on=Input(self.intersection_switch_id, "on"),
                page_filters=Input(self.page_filters_id, "data"),
            ),
        )
        def get_dynamic_chart(
            compute_percentage,
            main_tables,
            md_tables,
            optional,
        ):
            if not main_tables:
                return no_update

            main_tables: list[Base] = load_object(main_tables)
            md_tables: list[Base] = load_object(md_tables)
            page_filters: str = optional.get("page_filters", None)
            page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()

            base = base_data_subquery(
                main_tables=main_tables,
                meta_data_tables=md_tables,
                terms=[MetaData.dump_name, MetaData.clip_name, MetaData.grabindex],
                page_filters=page_filters,
                intersection_on=optional.get("intersection_on", False),
            )
            obj_query = (
                Query.from_(base)
                .groupby(base.dump_name, base.clip_name, base.grabindex)
                .select(base.dump_name, functions.Count("*", "objects_per_frame"))
            )
            query = (
                Query.from_(obj_query)
                .groupby(obj_query.dump_name, obj_query.objects_per_frame)
                .select(obj_query.dump_name, obj_query.objects_per_frame, functions.Count("*", "overall"))
            )
            if compute_percentage:
                query = CountGraph.percentage_wrapper(
                    query, query.overall, [query.dump_name], [query.objects_per_frame.as_("objects_per_frame")]
                )

            y_col = "percentage" if compute_percentage else "overall"
            data = execute(query)
            fig = basic_histogram_plot(data, "objects_per_frame", y_col, title="Objects Count")
            return fig
