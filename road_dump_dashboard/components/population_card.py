from dash import html, dcc, Input, Output, callback, no_update

from road_dump_dashboard.components.components_ids import DUMPS, POPULATION_DROPDOWN
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
    Input(DUMPS, "data"),
)
def init_population_options(dumps):
    if not dumps:
        return no_update, no_update, no_update

    options = [{"label": key.title(), "value": key} for key, value in dumps["tables"].items() if value]
    return options, options[0]["label"], options[0]["value"]
