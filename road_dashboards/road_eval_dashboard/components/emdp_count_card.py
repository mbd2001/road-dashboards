from dash import Input, Output, callback, html
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_eval_dashboard.components.components_ids import EMDP_COUNT, MD_FILTERS, NETS
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import generate_count_query
from road_dashboards.road_eval_dashboard.graphs.big_number import human_format_int

layout = card_wrapper(
    [html.Div([html.H3("Num EMDPs"), loading_wrapper([html.H1(id=EMDP_COUNT, style={"fontSize": "72px"})])])]
)


@callback(
    Output(EMDP_COUNT, "children"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_frame_count(meta_data_filters, nets):
    if not nets:
        return 0

    query = generate_count_query(nets["frame_tables"], nets["meta_data"], meta_data_filters=meta_data_filters)
    data, _ = query_athena(database="run_eval_db", query=query)
    return human_format_int(data.overall[0])
