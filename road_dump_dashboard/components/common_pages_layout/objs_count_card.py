from dash import MATCH, Input, Output, State, callback, html
from road_database_toolkit.athena.athena_utils import query_athena

from road_dump_dashboard.components.constants.components_ids import (
    INTERSECTION_SWITCH,
    MD_FILTERS,
    OBJS_COUNT,
    OBJS_MAIN_TABLE,
    OBJS_MD_TABLE,
    POPULATION_DROPDOWN,
    TABLES,
)
from road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper, loading_wrapper
from road_dump_dashboard.components.logical_components.queries_manager import generate_count_query
from road_dump_dashboard.graphs.big_number import human_format_int


def layout(objs_name, main_table, meta_data_table=None):
    objs_count_layout = card_wrapper(
        [
            html.Div(id=OBJS_MAIN_TABLE, children=main_table, style={"display": "none"}),
            html.Div(id=OBJS_MD_TABLE, children=meta_data_table, style={"display": "none"}),
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
    State(OBJS_MAIN_TABLE, "children"),
    State(OBJS_MD_TABLE, "children"),
    background=True,
)
def get_frame_count(meta_data_filters, tables, population, intersection_on, main_table, meta_data_table):
    if not population or not tables:
        return 0

    main_table = tables[main_table]
    meta_data_table = tables.get(meta_data_table)
    query = generate_count_query(
        main_table,
        population,
        intersection_on,
        meta_data_tables=meta_data_table,
        meta_data_filters=meta_data_filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    if len(tables["names"]) == 1:
        frame_count_str = human_format_int(data.overall[0])
    else:
        frame_count_str = "\n".join(
            [
                f"{dump_name.title()}: {human_format_int(amount)}"
                for dump_name, amount in zip(data.dump_name, data.overall)
            ]
        )

    return frame_count_str
