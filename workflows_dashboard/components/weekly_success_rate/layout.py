import dash_bootstrap_components as dbc
from dash import dcc, html

from workflows_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from workflows_dashboard.config import WEEKLY_SUCCESS_RATE_CHART

from . import callbacks  # DO NOT REMOVE!


def render_weekly_success_rate() -> dbc.Col:
    return dbc.Col(
        [
            card_wrapper(
                [
                    html.H3("Weekly Success Rate", className="card-title"),
                    loading_wrapper([dcc.Graph(id=WEEKLY_SUCCESS_RATE_CHART)]),
                ]
            )
        ],
        md=12,
    )
