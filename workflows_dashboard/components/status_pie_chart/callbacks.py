import pandas as pd
import plotly.express as px
from dash import Input, Output, callback

from workflows_dashboard.config import STATUS_PIE_CHART, WORKFLOW_DATA_STORE, WORKFLOW_SELECTOR, WORKFLOWS, ChartConfig
from workflows_dashboard.utils import add_center_annotation, create_empty_chart, format_workflow_name

chart_config = ChartConfig()


def create_status_pie_chart(df: pd.DataFrame, workflow_name: str):
    if df.empty:
        return create_empty_chart()

    status_counts = df["status"].value_counts()
    total_clips = len(df)

    if status_counts.empty:
        return create_empty_chart()

    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title=f"{format_workflow_name(workflow_name)} Status Distribution",
        color_discrete_map=chart_config.default_colors,
        color=status_counts.index,
    )

    add_center_annotation(fig, f"Total Clips:<br><b>{total_clips}</b>")

    return fig


for workflow in WORKFLOWS:

    @callback(
        Output(f"{STATUS_PIE_CHART}-{workflow}", "figure"),
        [Input(WORKFLOW_DATA_STORE, "data"), Input(WORKFLOW_SELECTOR, "value")],
        prevent_initial_call=True,
    )
    def update_pie_chart(data, selected_workflow, workflow_name=workflow):
        if not data or workflow_name not in data or workflow_name != selected_workflow:
            return create_empty_chart()

        df = pd.DataFrame(data[workflow_name])
        return create_status_pie_chart(df, workflow_name)
