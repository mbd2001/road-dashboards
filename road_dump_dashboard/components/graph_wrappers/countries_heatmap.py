import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html, no_update, register_page
from road_database_toolkit.athena.athena_utils import query_athena

from road_dump_dashboard.components.constants.components_ids import (
    COUNTRIES_DROPDOWN,
    COUNTRIES_HEAT_MAP,
    MD_FILTERS,
    POPULATION_DROPDOWN,
    TABLES,
)
from road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper, loading_wrapper
from road_dump_dashboard.components.logical_components.queries_manager import generate_count_query
from road_dump_dashboard.graphs.countries_map import (
    generate_world_map,
    iso_alpha_from_name,
    normalize_countries_count_to_percentiles,
    normalize_countries_names,
)

layout = html.Div(
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


@callback(
    Output(COUNTRIES_DROPDOWN, "options"),
    Output(COUNTRIES_DROPDOWN, "label"),
    Output(COUNTRIES_DROPDOWN, "value"),
    Input(TABLES, "data"),
)
def init_countries_dropdown(tables):
    if not tables:
        return no_update, no_update, no_update

    options = [{"label": name.title(), "value": name} for name in tables["names"]]
    return options, options[0]["label"], options[0]["value"]


@callback(
    Output(COUNTRIES_HEAT_MAP, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(COUNTRIES_DROPDOWN, "value"),
    background=True,
)
def get_countries_heat_map(meta_data_filters, tables, population, chosen_dump):
    if not population or not tables or not chosen_dump:
        return no_update

    main_tables = tables["meta_data"]
    group_by_column = "mdbi_country"
    query = generate_count_query(
        main_tables,
        population,
        False,
        meta_data_filters=meta_data_filters,
        group_by_column=group_by_column,
        dumps_to_include=chosen_dump,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data["normalized"] = normalize_countries_count_to_percentiles(data["overall"].to_numpy())
    data[group_by_column] = data[group_by_column].apply(normalize_countries_names)
    data["iso_alpha"] = data[group_by_column].apply(iso_alpha_from_name)
    fig = generate_world_map(
        countries_data=data, locations="iso_alpha", color="normalized", hover_data=["overall", group_by_column]
    )
    return fig
