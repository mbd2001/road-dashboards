import dash_bootstrap_components as dbc
from dash import html

from road_dashboards.workflows_dashboard.core_settings.constants import WORKFLOWS, ComponentIds
from road_dashboards.workflows_dashboard.utils.formatting import format_workflow_name


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
                ]
            )
        ]
    )
