from dash import Input, Output, State, callback, html, page_registry
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
from road_dashboards.road_dump_dashboard.graphs.big_number import human_format_int


def layout(objs_name):
    objs_count_layout = card_wrapper(
        [
            html.H3(f"Num {objs_name.title()}"),
            loading_wrapper(html.H4(id=OBJS_COUNT)),
        ],
    )
    return objs_count_layout


@callback(
    Output(OBJS_COUNT, "children"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    State(URL, "pathname"),
)
def get_frame_count(meta_data_filters, tables, population, intersection_on, pathname):
    if not population or not tables:
        return 0

    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    main_tables = tables[page_properties["main_table"]]
    meta_data_tables = tables.get(page_properties["meta_data_table"])
    query = generate_count_query(
        main_tables,
        population,
        intersection_on,
        [],
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    frame_count_str = "\n".join(
        [f"{dump_name.title()}: {human_format_int(amount)}" for dump_name, amount in zip(data.dump_name, data.overall)]
    )

    return frame_count_str
