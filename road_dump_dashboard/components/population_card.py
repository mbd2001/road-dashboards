from dash import html, dcc, Input, Output, callback, no_update

from road_dump_dashboard.components.components_ids import TABLES, POPULATION_DROPDOWN
from road_dump_dashboard.components.layout_wrapper import card_wrapper


layout = card_wrapper(
    [
        html.Div(
            [
                html.H3("Population"),
                dcc.Dropdown(
                    id=POPULATION_DROPDOWN,
                    style={"minWidth": "100%"},
                    multi=False,
                    placeholder="----",
                    value="",
                ),
            ]
        )
    ]
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
