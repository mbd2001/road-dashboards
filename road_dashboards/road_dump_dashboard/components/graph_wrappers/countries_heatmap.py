import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html, no_update
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    COUNTRIES_DROPDOWN,
    COUNTRIES_HEAT_MAP,
    MD_FILTERS,
    POPULATION_DROPDOWN,
    TABLES,
    URL,
)
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.components.logical_components.queries_manager import generate_count_query
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    get_curr_page_tables,
    get_existing_column,
    load_object,
)
from road_dashboards.road_dump_dashboard.graphs.countries_map import (
    generate_world_map,
    iso_alpha_from_name,
    normalize_countries_count_to_percentiles,
    normalize_countries_names,
)


def layout():
    countries_layout = html.Div(
        card_wrapper(
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
                dbc.Row(loading_wrapper(dcc.Graph(id=COUNTRIES_HEAT_MAP, config={"displayModeBar": False}))),
            ]
        )
    )
    return countries_layout


@callback(
    Output(COUNTRIES_DROPDOWN, "options"),
    Output(COUNTRIES_DROPDOWN, "label"),
    Output(COUNTRIES_DROPDOWN, "value"),
    Input(TABLES, "data"),
)
def init_countries_dropdown(tables):
    if not tables:
        return no_update, no_update, no_update

    tables = load_object(tables)
    options = {name.title(): name for name in tables.names}
    return options, options[0]["label"], options[0]["value"]


@callback(
    Output(COUNTRIES_HEAT_MAP, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(COUNTRIES_DROPDOWN, "value"),
    State(URL, "pathname"),
)
def get_countries_heat_map(meta_data_filters, tables, population, chosen_dump, pathname):
    if not population or not tables or not chosen_dump:
        return no_update

    main_tables, meta_data_tables = get_curr_page_tables(tables, pathname)
    group_by_column = get_existing_column("mdbi_country", main_tables, meta_data_tables)
    query = generate_count_query(
        main_tables,
        population,
        False,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        main_column=group_by_column,
        dumps_to_include=chosen_dump,
        extra_columns=[group_by_column],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data["normalized"] = normalize_countries_count_to_percentiles(data["overall"].to_numpy())
    data[group_by_column] = data[group_by_column].apply(normalize_countries_names)
    data["iso_alpha"] = data[group_by_column].apply(iso_alpha_from_name)
    fig = generate_world_map(
        countries_data=data, locations="iso_alpha", color="normalized", hover_data=["overall", group_by_column]
    )
    return fig
