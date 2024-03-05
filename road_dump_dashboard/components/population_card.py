from dash import html, dcc, Input, Output, callback

from road_dump_dashboard.components.components_ids import POPULATION_TABLES, POPULATION_DROPDOWN
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
    Input(POPULATION_TABLES, "data"),
)
def init_population_options(population_tables):
    if not population_tables:
        return []
    options = [{"label": key, "value": value} for key, value in population_tables.items()]
    return options
