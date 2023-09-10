from dash import html, callback, Input, Output, State

from road_eval_dashboard.components.components_ids import DP_COUNT, MD_FILTERS, NETS
from road_eval_dashboard.components.layout_wrapper import loading_wrapper, card_wrapper
from road_eval_dashboard.components.queries_manager import generate_count_query
from road_eval_dashboard.graphs.big_number import human_format_int
from road_database_toolkit.athena.athena_utils import query_athena

layout = card_wrapper(
    [html.Div([html.H3("Num Drivable Paths"), loading_wrapper([html.H1(id=DP_COUNT, style={"fontSize": "72px"})])])]
)


@callback(
    Output(DP_COUNT, "children"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_nets_dp_count(meta_data_filters, nets):
    if not nets:
        return 0

    query = generate_count_query(nets["pathnet_pred_table"], nets["meta_data"], meta_data_filters=meta_data_filters)
    data, _ = query_athena(database="run_eval_db", query=query)
    return human_format_int(data.overall[0])
