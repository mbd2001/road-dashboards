from dataclasses import dataclass
from typing import List

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html, no_update

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import Column
from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    COUNTRIES_DROPDOWN,
    COUNTRIES_HEAT_MAP,
    MAIN_TABLES,
    MD_TABLES,
    PAGE_FILTERS,
)
from road_dashboards.road_dump_dashboard.components.constants.queries_properties import BaseDataQuery, GroupByQuery
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import Table, load_object
from road_dashboards.road_dump_dashboard.graphs.countries_map import (
    generate_world_map,
    iso_alpha_from_name,
    normalize_countries_count_to_percentiles,
    normalize_countries_names,
)


@dataclass
class CountriesHeatMap(GridObject):
    """
    Defines the properties of group by graph

    Attributes:
            include_slider (bool): optional. True if the graph should include slider
            slider_default_value (int): optional. default value for the slider
    """

    title: str = COUNTRIES_HEAT_MAP
    full_grid_row: bool = True

    def layout(self):
        graph_row = super().layout()
        countries_layout = html.Div(
            [
                dbc.Row(
                    dcc.Dropdown(
                        id=COUNTRIES_DROPDOWN,
                        style={"minWidth": "100%"},
                        multi=False,
                        placeholder="----",
                        value="",
                    ),
                ),
                graph_row,
            ]
        )
        return countries_layout


@callback(
    Output(COUNTRIES_DROPDOWN, "options"),
    Output(COUNTRIES_DROPDOWN, "label"),
    Output(COUNTRIES_DROPDOWN, "value"),
    Input(MAIN_TABLES, "data"),
)
def init_countries_dropdown(main_tables):
    if not main_tables:
        return no_update, no_update, no_update

    main_tables: List[Table] = load_object(main_tables).tables
    options = {table.dataset_name: table.dataset_name.title() for table in main_tables}
    return options, main_tables[0].dataset_name.title(), main_tables[0].dataset_name


@callback(
    Output(COUNTRIES_HEAT_MAP, "figure"),
    Input(PAGE_FILTERS, "data"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
    Input(COUNTRIES_DROPDOWN, "value"),
)
def get_countries_heat_map(page_filters, main_tables, md_tables, chosen_dump):
    if not main_tables or not chosen_dump:
        return no_update

    main_tables: List[Table] = load_object(main_tables).tables
    md_tables: List[Table] = load_object(md_tables).tables if md_tables else None
    col_name = "mdbi_country"
    query = GroupByQuery(
        group_by_columns=[Column(col_name)],
        sub_query=BaseDataQuery(
            main_tables=main_tables,
            meta_data_tables=md_tables,
            page_filters=page_filters,
            dumps_to_include=[chosen_dump],
            extra_columns=[Column(col_name)],
        ),
    )
    output_name = query.metric.output_name
    data = query.get_results()
    data["normalized"] = normalize_countries_count_to_percentiles(data[output_name].to_numpy())
    data[col_name] = data[col_name].apply(normalize_countries_names)
    data["iso_alpha"] = data[col_name].apply(iso_alpha_from_name)
    fig = generate_world_map(
        countries_data=data, locations="iso_alpha", color="normalized", hover_data=[output_name, col_name]
    )
    return fig
