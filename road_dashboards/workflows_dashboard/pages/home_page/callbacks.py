from dash import Input, Output, callback
from road_database_toolkit.databases.workflows.workflow_enums import WorkflowType

from road_dashboards.workflows_dashboard.common.consts import ComponentIds


@callback(
    [Output(f"content-{workflow.value}", "style") for workflow in WorkflowType],
    [Input(ComponentIds.WORKFLOW_SELECTOR, "value")],
)
def update_content(selected_workflow: str):
    return [
        {"display": "block"} if workflow.value == selected_workflow else {"display": "none"}
        for workflow in WorkflowType
    ]


@callback([Output(f"workflow-tab-{workflow.value}", "active") for workflow in WorkflowType], Input("url", "hash"))
def set_active_tab(hash_value):
    if not hash_value:
        active_workflow = WorkflowType.GTRM
    else:
        active_workflow = hash_value.replace("#", "")

    if active_workflow not in WorkflowType:
        active_workflow = WorkflowType.GTRM

    return [workflow == active_workflow for workflow in WorkflowType]
