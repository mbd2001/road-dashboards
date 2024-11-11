from dash import Input, Output, callback

from road_dashboards.workflows_dashboard.core_settings.constants import BRAIN_OPTIONS, WORKFLOWS, ComponentIds
from road_dashboards.workflows_dashboard.database.workflow_manager import WorkflowsDBManager

workflow_db_handler = WorkflowsDBManager()


@callback(
    Output(ComponentIds.WORKFLOW_DATA_STORE, "data"),
    [
        Input("url", "pathname"),
        Input(ComponentIds.BRAIN_SELECTOR, "value"),
        Input(ComponentIds.DATE_RANGE_PICKER, "start_date"),
        Input(ComponentIds.DATE_RANGE_PICKER, "end_date"),
    ],
)
def update_data(pathname, selected_brains, start_date, end_date):
    if not selected_brains:
        selected_brains = BRAIN_OPTIONS

    return workflow_db_handler.get_all_workflow_data(
        brain_types=selected_brains, start_date=start_date, end_date=end_date
    )


@callback(
    [Output(f"content-{workflow}", "style") for workflow in WORKFLOWS], [Input(ComponentIds.WORKFLOW_SELECTOR, "value")]
)
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
