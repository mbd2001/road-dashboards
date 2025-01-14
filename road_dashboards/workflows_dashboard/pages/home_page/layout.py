import dash_bootstrap_components as dbc
from dash import dcc, html, register_page

from road_dashboards.workflows_dashboard.components.filters.layout import render_filters
from road_dashboards.workflows_dashboard.components.main_content.layout import render_main_content
from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds, LoadingStyles
from road_dashboards.workflows_dashboard.database.workflow_manager import WorkflowsDBManager

from . import callbacks  # DO NOT REMOVE!

register_page(__name__, path="/", name="Workflow Status", order=1)

workflow_db_handler = WorkflowsDBManager()

layout = html.Div(
    [
        # Loading overlay
        dbc.Spinner(
            html.Div(id=ComponentIds.LOADING_OVERLAY),
            color="primary",
            spinner_style=LoadingStyles.spinner,
        ),
        # Main content
        html.Div(
            [
                html.H1("Workflow Status Dashboard", className="mb-5 text-center text-lg-start"),
                dcc.Store(id=ComponentIds.WORKFLOW_DATA_STORE, data={}),
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
