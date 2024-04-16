from dash import Input, Output, callback, dcc, html, no_update

from road_dump_dashboard.components.constants.components_ids import POPULATION_DROPDOWN, TABLES
from road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper

layout = card_wrapper(
    [
        html.H3("Population"),
        dcc.Dropdown(
            id=POPULATION_DROPDOWN,
            multi=False,
            placeholder="----",
            value="",
        ),
    ],
)


@callback(
    Output(POPULATION_DROPDOWN, "options"),
    Output(POPULATION_DROPDOWN, "label"),
    Output(POPULATION_DROPDOWN, "value"),
    Input(TABLES, "data"),
)
def init_population_options(tables):
    if not tables:
        return no_update, no_update, no_update

    populations = ["test", "train", "all"]
    options = [{"label": population.title(), "value": population} for population in populations]
    return options, "All", "all"
