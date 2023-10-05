from dash import html, callback, Input, Output

from road_dump_dashboard.components.components_ids import POPULATION_STATE, MD_TABLE
from road_dump_dashboard.components.layout_wrapper import card_wrapper


# layout = card_wrapper([html.Div([html.H3("Population"), html.H1(id=POPULATION_STATE, style={"fontSize": "72px"})])])


# @callback(
#     Output(POPULATION_STATE, "children"),
#     Input(MD_TABLE, "data"),
# )
# def get_obj_count(md_table):
#     if not md_table:
#         return "-"
#
#     return nets["population"]

layout = card_wrapper([html.Div([html.H3("Population"), html.H1(id=POPULATION_STATE, style={"fontSize": "72px"})])])


@callback(
    Output(POPULATION_STATE, "children"),
    Input(MD_TABLE, "data"),
)
def get_obj_count(md_table):
    if not md_table:
        return "-"

    return "Test"
