from dash import html, callback, Input, Output, State

from road_dump_dashboard.components.components_ids import FRAME_COUNT, MD_FILTERS, MD_TABLE
from road_dump_dashboard.components.layout_wrapper import loading_wrapper, card_wrapper
from road_dump_dashboard.components.queries_manager import generate_count_query
from road_dump_dashboard.graphs.big_number import human_format_int
from road_database_toolkit.athena.athena_utils import query_athena

layout = card_wrapper(
    [html.Div([html.H3("Num Frames"), loading_wrapper([html.H1(id=FRAME_COUNT, style={"fontSize": "72px"})])])]
)


@callback(
    Output(FRAME_COUNT, "children"),
    Input(MD_FILTERS, "data"),
    State(MD_TABLE, "data"),
    background=True,
)
def get_frame_count(meta_data_filters, md_table):
    if not md_table:
        return 0

    query = generate_count_query(md_table, meta_data_filters=meta_data_filters)
    data, _ = query_athena(database="run_eval_db", query=query)
    return human_format_int(data.overall[0])
