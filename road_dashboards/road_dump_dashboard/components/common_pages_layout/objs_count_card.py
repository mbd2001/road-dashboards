import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html, no_update, page_registry
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    INTERSECTION_SWITCH,
    MD_FILTERS,
    OBJS_COUNT,
    POPULATION_DROPDOWN,
    TABLES,
    URL,
)
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.components.logical_components.queries_manager import generate_count_query
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import get_curr_page_tables


def layout():
    objs_count_layout = card_wrapper(
        loading_wrapper(dbc.Accordion(id=OBJS_COUNT, always_open=True)),
    )
    return objs_count_layout


@callback(
    Output(OBJS_COUNT, "children"),
    Output(OBJS_COUNT, "active_item"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    State(URL, "pathname"),
)
def get_frame_count(meta_data_filters, tables, population, intersection_on, pathname):
    if not population or not tables:
        return no_update, no_update

    main_tables, meta_data_tables = get_curr_page_tables(tables, pathname)
    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    objs_name = page_properties["objs_name"]
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        [],
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    frame_count_accordion = [
        dbc.AccordionItem(
            html.H5(f"{amount} {objs_name.title()}"),
            title=dump_name.title(),
            item_id=dump_name,
        )
        for dump_name, amount in zip(data.dump_name, data.overall)
    ]
    return frame_count_accordion, list(data.dump_name)
