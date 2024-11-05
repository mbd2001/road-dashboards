import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback

from workflows_dashboard.config import WEEKLY_SUCCESS_RATE_CHART, WORKFLOW_DATA_STORE, WORKFLOWS
from workflows_dashboard.utils import create_empty_chart, format_workflow_name


def prepare_weekly_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare weekly statistics from workflow data.

    Args:
        df (pd.DataFrame): Raw workflow data containing 'last_update' and 'status' columns

    Returns:
        pd.DataFrame: Weekly aggregated statistics with columns for SUCCESS and FAILED counts
        Empty DataFrame if input is empty
    """
    if df.empty:
        return pd.DataFrame()

    required_columns = ['last_update', 'status']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"DataFrame must contain columns: {required_columns}")

    df["last_update"] = pd.to_datetime(df["last_update"])

    # Group data by week and status, counting occurrences
    # W-SUN: Week starts on Sunday and ends on Saturday
    weekly_stats = (
        df.groupby([pd.Grouper(key="last_update", freq="W-SUN", closed="left", label="left"), "status"])
        .size()
        .unstack(fill_value=0)
    )

    for status in ["SUCCESS", "FAILED"]:
        if status not in weekly_stats.columns:
            weekly_stats[status] = 0

    return weekly_stats


def calculate_success_rate(weekly_stats: pd.DataFrame) -> pd.Series:
    """Calculate success rate from weekly statistics.

    Args:
        weekly_stats (pd.DataFrame): DataFrame containing SUCCESS and FAILED columns

    Returns:
        pd.Series: Weekly success rates as percentages (0-100)
    """
    # Calculate total runs per week and success percentage
    total_weekly = weekly_stats["SUCCESS"] + weekly_stats["FAILED"]
    success_rate = (weekly_stats["SUCCESS"] / total_weekly * 100).round(2)
    return success_rate.fillna(0)


def create_multi_workflow_chart(data: dict) -> go.Figure:
    """Create a line chart comparing multiple workflows' success rates.

    Args:
        data (dict): Dictionary mapping workflow names to their raw data

    Returns:
        go.Figure: Plotly figure object containing the multi-line chart
    """
    fig = go.Figure()

    marker_symbols = ["circle", "square", "diamond", "triangle-up", "star"]

    for idx, workflow in enumerate(WORKFLOWS):
        if workflow not in data:
            continue

        df = pd.DataFrame(data[workflow])
        if df.empty:
            continue

        weekly_stats = prepare_weekly_data(df)
        weekly_stats["success_rate"] = calculate_success_rate(weekly_stats)

        # Prepare hover text with formatted date ranges and success rates
        weekly_stats["week_end"] = weekly_stats.index + pd.Timedelta(days=6)
        hover_text = [
            f"{format_workflow_name(workflow)}<br>"
            f"{start.strftime('%d.%m')} - {end.strftime('%d.%m')}<br>"
            f"Success Rate: {rate:.1f}%"
            for start, end, rate in zip(weekly_stats.index, weekly_stats["week_end"], weekly_stats["success_rate"])
        ]

        # Add trace for each workflow
        fig.add_trace(
            go.Scatter(
                x=weekly_stats.index,
                y=weekly_stats["success_rate"],
                name=format_workflow_name(workflow),
                mode="lines+markers",
                line=dict(width=2),
                opacity=0.8,
                marker=dict(size=8, symbol=marker_symbols[idx % len(marker_symbols)]),
                text=hover_text,
                hovertemplate="%{text}<extra></extra>",
            )
        )

    # Configure layout with fixed y-axis range and proper labels
    fig.update_layout(
        yaxis_range=[0, 100],
        yaxis_title="Success Rate (%)",
        xaxis_title="Week",
        hovermode="x unified",
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    return fig


@callback(Output(WEEKLY_SUCCESS_RATE_CHART, "figure"), Input(WORKFLOW_DATA_STORE, "data"))
def update_weekly_success_rate(data: dict) -> go.Figure:
    """Update the weekly success rate chart showing all workflows.

    Args:
        data (dict): Dictionary containing workflow data from the data store

    Returns:
        go.Figure: Updated chart figure, or empty chart if no data available
    """
    if not data:
        return create_empty_chart()

    return create_multi_workflow_chart(data)
