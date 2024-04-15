from dash import Input, Output, State, callback, html
from road_database_toolkit.athena.athena_utils import query_athena

from road_eval_dashboard.components.components_ids import DP_COUNT, MD_FILTERS, NETS, PATHNET_PRED
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components.queries_manager import generate_count_query
from road_eval_dashboard.graphs.big_number import human_format_int

layout = card_wrapper(
    [html.Div([html.H3("Num Drivable Paths"), loading_wrapper([html.H1(id=DP_COUNT, style={"fontSize": "72px"})])])]
)


@callback(
    Output(DP_COUNT, "children"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    background=True,
)
def get_nets_dp_count(meta_data_filters, nets):
    if not nets:
        return 0

    query = generate_count_query(nets[PATHNET_PRED], nets["meta_data"], meta_data_filters=meta_data_filters)
    data, _ = query_athena(database="run_eval_db", query=query)
    return human_format_int(data.overall[0])
