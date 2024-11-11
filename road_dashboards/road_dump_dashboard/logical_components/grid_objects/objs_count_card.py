import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html, no_update
from pypika import Criterion, Query, functions

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import base_data_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import FormatNumber, execute, load_object
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class ObjCountCard(GridObject):
    def __init__(
        self,
        main_table: str,
        objs_name: str,
        page_filters_id: str,
        intersection_switch_id: str,
        full_grid_row: bool = False,
        component_id: str = "",
    ):
        self.main_table = main_table
        self.objs_name = objs_name
        self.page_filters_id = page_filters_id
        self.intersection_switch_id = intersection_switch_id
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.obj_count_id = self._generate_id("obj_count")

    def layout(self):
        return card_wrapper(loading_wrapper(dbc.Accordion(id=self.obj_count_id, always_open=True)))

    def _callbacks(self):
        @callback(
            Output(self.obj_count_id, "children"),
            Output(self.obj_count_id, "active_item"),
            Input(self.page_filters_id, "data"),
            Input(self.main_table, "data"),
            Input(META_DATA, "data"),
            Input(self.intersection_switch_id, "on"),
        )
        def get_obj_count(page_filters, main_tables, md_tables, intersection_on):
            if not main_tables:
                return no_update, no_update

            main_tables: list[Base] = load_object(main_tables)
            md_tables: list[Base] = load_object(md_tables) if md_tables else None
            page_filters: Criterion = load_object(page_filters)
            base = base_data_subquery(
                main_tables=main_tables,
                terms=[MetaData.dump_name],
                meta_data_tables=md_tables,
                page_filters=page_filters,
                intersection_on=intersection_on,
            )
            query = (
                Query.from_(base)
                .groupby(MetaData.dump_name)
                .select(MetaData.dump_name, FormatNumber(functions.Count("*"), alias="overall"))
            )
            data = execute(query)
            frame_count_accordion = [
                dbc.AccordionItem(
                    html.H5(f"{amount} {self.objs_name.title()}"),
                    title=dump_name.title(),
                    item_id=dump_name,
                )
                for dump_name, amount in zip(data.dump_name, data.overall)
            ]
            return frame_count_accordion, list(data.dump_name)
