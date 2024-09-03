from dash import dcc, html

from road_dashboards.road_dump_dashboard.components.constants.components_ids import POPULATION_DROPDOWN
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper

populations = ["all", "test", "train"]

layout = card_wrapper(
    [
        html.H3("Population"),
        dcc.Dropdown(
            options={population: population.title() for population in populations},
            value=populations[0],
            id=POPULATION_DROPDOWN,
            multi=False,
            placeholder="----",
        ),
    ],
)
