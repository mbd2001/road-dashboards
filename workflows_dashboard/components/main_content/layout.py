import dash_bootstrap_components as dbc
from dash import dcc, html

from workflows_dashboard.components.error_pie_chart.layout import render_error_pie_chart
from workflows_dashboard.components.status_pie_chart.layout import render_status_pie_chart
from workflows_dashboard.components.weekly_success_rate.layout import render_weekly_success_rate
from workflows_dashboard.config import DOWNLOAD_DATAFRAME, EXPORT_BUTTON, WORKFLOW_SELECTOR, WORKFLOWS
from workflows_dashboard.utils import format_workflow_name

from . import callbacks  # DO NOT DELETE!!!


def create_workflow_selector():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Select Workflow", className="mb-2"),
                            dbc.RadioItems(
                                id=WORKFLOW_SELECTOR,
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
                    dbc.Col(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-download me-2"), "Export Data"],
                                id=EXPORT_BUTTON,
                                color="primary",
                                className="float-end",
                            ),
                            dcc.Download(id=DOWNLOAD_DATAFRAME),
                        ],
                        width="auto",
                    ),
                ]
            )
        ]
    )


def create_workflow_content() -> html.Div:
    return html.Div(
        [
            dbc.Row([render_weekly_success_rate()], className="g-4 mb-4"),
            create_workflow_selector(),
            *[
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col([render_status_pie_chart(workflow)], md=6),
                                dbc.Col([render_error_pie_chart(workflow)], md=6),
                            ],
                            className="g-4",
                        )
                    ],
                    id=f"content-{workflow}",
                )
                for workflow in WORKFLOWS
            ],
        ]
    )


def render_main_content() -> dbc.Col:
    return dbc.Col([html.Div([create_workflow_content()]), html.Div(id="workflow-content")], width=10)
