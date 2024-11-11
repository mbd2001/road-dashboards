import dash_bootstrap_components as dbc
from dash import dcc, html

from road_dashboards.workflows_dashboard.core_settings.constants import WORKFLOWS, ComponentIds
from road_dashboards.workflows_dashboard.utils.formatting import format_workflow_name

from . import callbacks  # DO NOT REMOVE!!


def create_workflow_selector():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Select Workflow", className="mb-2"),
                            dbc.RadioItems(
                                id=ComponentIds.WORKFLOW_SELECTOR,
                                options=[
                                    {"label": format_workflow_name(workflow), "value": workflow}
                                    for workflow in WORKFLOWS
                                ],
                                value=WORKFLOWS[0],
                                inline=True,
                                className="mb-4",
                            ),
                        ]
                    ),
                    create_export_section(),
                ]
            )
        ]
    )


def create_export_section():
    return dbc.Col(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Dropdown(
                            id=ComponentIds.EXPORT_WORKFLOW_SELECTOR,
                            options=[
                                {"label": format_workflow_name(workflow), "value": workflow} for workflow in WORKFLOWS
                            ],
                            value=WORKFLOWS,
                            multi=True,
                            clearable=False,
                            className="me-3",
                            style={"width": "330px"},
                        ),
                        width="auto",
                    ),
                    dbc.Col(
                        dbc.Button(
                            [html.I(className="fas fa-download me-2"), "Export Data"],
                            id=ComponentIds.EXPORT_BUTTON,
                            color="primary",
                        ),
                        width="auto",
                    ),
                ],
                className="float-end g-2",
            ),
            dcc.Download(id=ComponentIds.DOWNLOAD_DATAFRAME),
        ],
        width="auto",
    )
