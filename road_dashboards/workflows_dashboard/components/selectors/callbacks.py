from datetime import datetime

from dash import Input, Output, State, callback, dcc

from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds
from road_dashboards.workflows_dashboard.database.workflow_manager import WorkflowsDBManager

workflow_db_handler = WorkflowsDBManager()


@callback(
    Output(ComponentIds.DOWNLOAD_DATAFRAME, "data"),
    Input(ComponentIds.EXPORT_BUTTON, "n_clicks"),
    [
        State(ComponentIds.BRAIN_SELECTOR, "value"),
        State(ComponentIds.DATE_RANGE_PICKER, "start_date"),
        State(ComponentIds.DATE_RANGE_PICKER, "end_date"),
        State(ComponentIds.EXPORT_WORKFLOW_SELECTOR, "value"),
    ],
    prevent_initial_call=True,
)
def export_data(n_clicks, brain_types, start_date, end_date, selected_workflows):
    if not n_clicks or not selected_workflows:
        return None

    df = workflow_db_handler.get_workflow_export_data(
        workflows=selected_workflows, brain_types=brain_types, start_date=start_date, end_date=end_date
    )

    if df.empty:
        return None

    current_date = datetime.now().strftime("%d-%m-%Y")
    filename = f"{'_'.join(selected_workflows)}_data_{current_date}.csv"
    return dcc.send_data_frame(df.to_csv, filename, index=False)
