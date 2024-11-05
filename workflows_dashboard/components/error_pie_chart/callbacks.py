import pandas as pd
import plotly.express as px
from dash import Input, Output, callback

from workflows_dashboard.config import ERROR_PIE_CHART, WORKFLOW_DATA_STORE, WORKFLOW_SELECTOR, WORKFLOWS
from workflows_dashboard.utils import add_center_annotation, create_empty_chart, format_workflow_name


def create_error_pie_chart(df: pd.DataFrame, workflow_name: str) -> px.pie:
    if df.empty:
        return create_empty_chart()

    failed_df = df[df["status"] == "FAILED"]
    if failed_df.empty:
        return create_empty_chart()

    error_counts = failed_df["message"].value_counts()
    total_failed_clips = len(failed_df)

    fig = px.pie(
        values=error_counts.values,
        names=error_counts.index,
        title=f"{format_workflow_name(workflow_name)} Error Distribution",
    )

    add_center_annotation(fig, f"Total Clips:<br><b>{total_failed_clips}</b>")

    return fig


for workflow in WORKFLOWS:

    @callback(
        Output(f"{ERROR_PIE_CHART}-{workflow}", "figure"),
        [Input(WORKFLOW_DATA_STORE, "data"), Input(WORKFLOW_SELECTOR, "value")],
    )
    def update_error_chart(data, selected_workflow, workflow_name=workflow):
        if not data or workflow_name not in data or workflow_name != selected_workflow:
            return create_empty_chart()
        return create_error_pie_chart(pd.DataFrame(data[workflow_name]), workflow_name)
