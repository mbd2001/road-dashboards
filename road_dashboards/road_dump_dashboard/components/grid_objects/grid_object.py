from dataclasses import dataclass

import dash_bootstrap_components as dbc
from dash import dcc

from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import loading_wrapper


@dataclass(kw_only=True)
class GridObject:
    """
    Defines the base properties of a single graph

    Attributes:
            name (str): the name of the graph, used for the title and the id
            full_grid_row (bool): optional.
    """

    title: str
    full_grid_row: bool = False

    def layout(self):
        graph = loading_wrapper(
            dcc.Graph(
                id=self.title,
                config={"displayModeBar": False},
            )
        )
        return dbc.Row([graph])
