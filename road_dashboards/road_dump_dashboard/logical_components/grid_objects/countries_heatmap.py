import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, no_update
from pypika import Criterion, Query, functions

from road_dashboards.road_dump_dashboard.graphical_components.countries_map import (
    generate_world_map,
    iso_alpha_from_name,
    normalize_countries_count_to_percentiles,
    normalize_countries_names,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import loading_wrapper
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import base_data_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import execute, load_object
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class CountriesHeatMap(GridObject):
    """
    Defines the properties of countries heatmap.
    """

    def __init__(
        self,
        main_table: str,
        page_filters_id: str,
        datasets_dropdown_id: str,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.main_table = main_table
        self.page_filters_id = page_filters_id
        self.datasets_dropdown_id = datasets_dropdown_id
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.heatmap_id = self._generate_id("heatmap")

    def layout(self):
        countries_layout = dbc.Row(
            loading_wrapper(
                dcc.Graph(
                    id=self.heatmap_id,
                    config={"displayModeBar": False},
                )
            )
        )
        return countries_layout

    def _callbacks(self):
        @callback(
            Output(self.heatmap_id, "figure"),
            Input(self.page_filters_id, "data"),
            Input(self.main_table, "data"),
            Input(META_DATA, "data"),
            Input(self.datasets_dropdown_id, "value"),
        )
        def get_countries_heat_map(page_filters, main_tables, md_tables, chosen_dump):
            if not main_tables or not chosen_dump:
                return no_update

            main_tables: list[Base] = load_object(main_tables)
            md_tables: list[Base] = load_object(md_tables) if md_tables else None
            page_filters: Criterion = load_object(page_filters)
            country_col = MetaData.mdbi_country
            base = base_data_subquery(
                main_tables=[table for table in main_tables if table.dataset_name == chosen_dump],
                terms=[country_col],
                meta_data_tables=[table for table in md_tables if table.dataset_name == chosen_dump],
                page_filters=page_filters,
            )
            query = Query.from_(base).groupby(country_col).select(country_col, functions.Count("*", "overall"))
            data = execute(query)
            data["normalized"] = normalize_countries_count_to_percentiles(data["overall"].to_numpy())
            data[country_col.alias] = data[country_col.alias].apply(normalize_countries_names)
            data["iso_alpha"] = data[country_col.alias].apply(iso_alpha_from_name)
            fig = generate_world_map(
                countries_data=data,
                locations="iso_alpha",
                color="normalized",
                hover_data=["overall", country_col.alias],
            )
            return fig
