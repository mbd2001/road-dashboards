import dash_bootstrap_components as dbc
from dash import dcc, html

from workflows_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from workflows_dashboard.config import ERROR_PIE_CHART

from . import callbacks  # DO NOT REMOVE!


def render_error_pie_chart(workflow_name: str) -> dbc.Col:
    chart_id = f"{ERROR_PIE_CHART}-{workflow_name}"

    return dbc.Col([card_wrapper([loading_wrapper([dcc.Graph(id=chart_id)])])], md=12)
