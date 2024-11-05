import dash_bootstrap_components as dbc
from dash import dcc, html, register_page

from workflows_dashboard.components.main_content.layout import render_main_content
from workflows_dashboard.components.sidebar.layout import render_sidebar
from workflows_dashboard.config import WORKFLOW_DATA_STORE
from workflows_dashboard.workflows_db_manager import WorkflowsDBManager

from . import callbacks  # DO NOT REMOVE!

register_page(__name__, path="/", name="Workflow Status", order=1)

workflow_db_handler = WorkflowsDBManager()

layout = html.Div(
    [
        html.H1("Workflow Status Dashboard", className="mb-5"),
        dcc.Store(id=WORKFLOW_DATA_STORE, data={}),
        dbc.Row([render_sidebar(), render_main_content()]),
    ]
)
