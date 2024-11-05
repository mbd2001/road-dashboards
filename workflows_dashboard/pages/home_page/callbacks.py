from dash import Input, Output, callback

from workflows_dashboard.config import (
    BRAIN_SELECTOR,
    DATE_RANGE_PICKER,
    WORKFLOW_DATA_STORE,
    WORKFLOW_SELECTOR,
    WORKFLOWS,
)
from workflows_dashboard.workflows_db_manager import WorkflowsDBManager

workflow_db_handler = WorkflowsDBManager()


@callback(
    Output(WORKFLOW_DATA_STORE, "data"),
    [
        Input("url", "pathname"),
        Input(BRAIN_SELECTOR, "value"),
        Input(DATE_RANGE_PICKER, "start_date"),
        Input(DATE_RANGE_PICKER, "end_date"),
    ],
)
def initialize_data(pathname, selected_brains, start_date, end_date):
    data = {}
    workflow_data = workflow_db_handler.get_multiple_workflow_data(WORKFLOWS, selected_brains, start_date, end_date)
    for workflow in WORKFLOWS:
        data[workflow] = workflow_data[workflow].to_dict("records")
    return data


@callback([Output(f"content-{workflow}", "style") for workflow in WORKFLOWS], [Input(WORKFLOW_SELECTOR, "value")])
def update_content(selected_workflow):
    return [{"display": "block"} if workflow == selected_workflow else {"display": "none"} for workflow in WORKFLOWS]


@callback([Output(f"workflow-tab-{workflow}", "active") for workflow in WORKFLOWS], Input("url", "hash"))
def set_active_tab(hash_value):
    if not hash_value:
        active_workflow = WORKFLOWS[0]
    else:
        active_workflow = hash_value.replace("#", "")

    if active_workflow not in WORKFLOWS:
        active_workflow = WORKFLOWS[0]

    return [workflow == active_workflow for workflow in WORKFLOWS]
