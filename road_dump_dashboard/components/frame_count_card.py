from dash import html, callback, Input, Output, State

from road_dump_dashboard.components.components_ids import (
    FRAME_COUNT,
    MD_FILTERS,
    POPULATION_DROPDOWN,
    INTERSECTION_SWITCH,
    DUMPS,
)
from road_dump_dashboard.components.layout_wrapper import loading_wrapper, card_wrapper
from road_dump_dashboard.components.queries_manager import generate_count_query
from road_dump_dashboard.graphs.big_number import human_format_int
from road_database_toolkit.athena.athena_utils import query_athena

layout = card_wrapper([html.Div([html.H3("Num Frames"), loading_wrapper([html.H3(id=FRAME_COUNT)])])])


@callback(
    Output(FRAME_COUNT, "children"),
    Input(MD_FILTERS, "data"),
    State(DUMPS, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(INTERSECTION_SWITCH, "on"),
    background=True,
)
def get_frame_count(meta_data_filters, dumps, population, intersection_on):
    if not population or not dumps:
        return 0

    md_tables = dumps["tables"]["meta_data"].values()
    query = generate_count_query(
        md_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    if intersection_on:
        frame_count_str = f"Intersection Count: {human_format_int(data.overall[0])}"
    elif len(dumps["names"]) == 1:
        frame_count_str = human_format_int(data.overall[0])
    else:
        frame_count_str = "\n".join(
            [
                f"{dump_name.title()}: {human_format_int(amount)}"
                for dump_name, amount in zip(data.dump_name, data.overall)
            ]
        )

    return frame_count_str
