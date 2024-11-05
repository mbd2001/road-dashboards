import pandas as pd
import plotly.express as px
from dash import Input, Output, callback

from workflows_dashboard.config import ERROR_PIE_CHART, WORKFLOW_DATA_STORE, WORKFLOW_SELECTOR, WORKFLOWS, MAX_ERROR_MESSAGE_LENGTH
from workflows_dashboard.utils import add_center_annotation, create_empty_chart, format_workflow_name

def truncate_error_message(message):
    if len(message) > MAX_ERROR_MESSAGE_LENGTH:
        return message[:MAX_ERROR_MESSAGE_LENGTH] + '...'
    return message

def create_error_pie_chart(df: pd.DataFrame, workflow_name: str) -> px.pie:
    if df.empty:
        return create_empty_chart()

    failed_df = df[df["status"] == "FAILED"]
    if failed_df.empty:
        return create_empty_chart()

    failed_df = failed_df.copy()
    failed_df["truncated_message"] = failed_df["message"].apply(truncate_error_message)
    message_mapping = dict(zip(failed_df["truncated_message"], failed_df["message"]))

    error_counts = failed_df["truncated_message"].value_counts()
    total_failed_clips = len(failed_df)

    plot_df = pd.DataFrame({
        'count': error_counts.values,
        'message': error_counts.index,
        'full_message': [message_mapping[name] for name in error_counts.index]
    })

    fig = px.pie(
        plot_df,
        values='count',
        names='message',
        title=f"{format_workflow_name(workflow_name)} Error Distribution",
        custom_data=['full_message']
    )

    add_center_annotation(fig, f"Total Clips:<br><b>{total_failed_clips}</b>")

    fig.update_traces(
        textposition='inside',
        textinfo='percent',
        insidetextfont=dict(size=10),
        hovertemplate="<b>Full Error:</b><br>%{customdata[0]}<br><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"
    )

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
