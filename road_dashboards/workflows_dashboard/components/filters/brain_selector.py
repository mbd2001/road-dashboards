import dash_bootstrap_components as dbc
from dash import dcc, html

from road_dashboards.workflows_dashboard.core_settings.constants import BRAIN_OPTIONS, ComponentIds


def render_brain_selector():
    return html.Div(
        [
            html.H6("Brain Selection", className="text-muted small mb-1 text-center"),
            dcc.Dropdown(
                id=ComponentIds.BRAIN_SELECTOR,
                options=[{"label": brain_type.upper(), "value": brain_type} for brain_type in BRAIN_OPTIONS],
                value=[BRAIN_OPTIONS[0]],
                multi=True,
                clearable=False,
                className="border-0",
                style={"minWidth": "6rem", "height": "48px", "padding": "0 8px"},
            ),
        ],
        className="d-flex flex-column align-items-center me-3",
    )
