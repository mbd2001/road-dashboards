import dash_bootstrap_components as dbc
from dash import html
from road_database_toolkit.databases.workflows.workflow_enums import WorkflowType

from road_dashboards.workflows_dashboard.common.consts import ComponentIds
from road_dashboards.workflows_dashboard.common.utils import format_workflow_type


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
                                    {"label": format_workflow_type(workflow_type), "value": workflow_type.value}
                                    for workflow_type in WorkflowType
                                ],
                                value=WorkflowType.GTRM.value,
                                inline=True,
                                className="mb-4",
                            ),
                        ]
                    ),
                ]
            )
        ]
    )
