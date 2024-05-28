from dash import Input, Output, callback, html

from road_eval_dashboard.road_eval_dashboard.components.components_ids import NETS, POPULATION_STATE
from road_eval_dashboard.road_eval_dashboard.components.layout_wrapper import card_wrapper

layout = card_wrapper([html.Div([html.H3("Population"), html.H1(id=POPULATION_STATE, style={"fontSize": "72px"})])])


@callback(
    Output(POPULATION_STATE, "children"),
    Input(NETS, "data"),
)
def get_obj_count(nets):
    if not nets:
        return "-"

    return nets["population"]
