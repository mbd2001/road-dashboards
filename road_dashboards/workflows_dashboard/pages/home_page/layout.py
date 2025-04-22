import dash_bootstrap_components as dbc
from dash import dcc, html, register_page

from road_dashboards.workflows_dashboard.common.consts import ComponentIds, LoadingStyles
from road_dashboards.workflows_dashboard.components.filters.layout import render_filters
from road_dashboards.workflows_dashboard.components.main_content.layout import render_main_content

from . import callbacks  # noqa: F401

register_page(__name__, path="/", name="Workflow Status", order=1)


layout = html.Div(
    [
        dbc.Spinner(
            html.Div(id=ComponentIds.LOADING_OVERLAY),
            color="primary",
            spinner_style=LoadingStyles.spinner,
        ),
        dcc.Store(id=ComponentIds.WORKFLOW_DATA_STORE, data={}),
        dcc.Store(id="refresh-trigger-store", data=0),
        html.Div(
            [
                html.H1("Workflow Status Dashboard", className="mb-5 text-center text-lg-start"),
                render_filters(),
                dbc.Row(
                    [render_main_content()],
                    className="g-4 h-100",
                ),
            ],
            id=ComponentIds.MAIN_CONTENT,
            className="d-flex flex-column h-100",
        ),
    ]
)
