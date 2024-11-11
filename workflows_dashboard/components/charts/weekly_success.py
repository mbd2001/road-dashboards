import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback

from workflows_dashboard.components.base.chart import BaseChart
from workflows_dashboard.core_settings.constants import WORKFLOWS, ComponentIds, Status
from workflows_dashboard.core_settings.settings import ChartSettings
from workflows_dashboard.utils.formatting import format_workflow_name


class WeeklySuccessChart(BaseChart):
    def __init__(self):
        super().__init__(ComponentIds.WEEKLY_SUCCESS_RATE_CHART)
        self.marker_symbols = ChartSettings.marker_symbols

    def prepare_weekly_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare weekly statistics from workflow data.

        Args:
            df: DataFrame containing workflow data

        Returns:
            DataFrame with weekly statistics
        """
        if df.empty:
            return pd.DataFrame()

        df["last_update"] = pd.to_datetime(df["last_update"])
        weekly_stats = (
            df.groupby([pd.Grouper(key="last_update", freq="W-SUN", closed="left", label="left"), "status"])
            .size()
            .unstack(fill_value=0)
        )

        for status in [Status.SUCCESS.value, Status.FAILED.value]:
            if status not in weekly_stats.columns:
                weekly_stats[status] = 0

        return weekly_stats

    def calculate_success_rate(self, stats: pd.DataFrame) -> pd.Series:
        total = stats[Status.SUCCESS.value] + stats[Status.FAILED.value]
        return (stats[Status.SUCCESS.value] / total * 100).fillna(0)

    def create_chart(self, data: dict) -> go.Figure:
        if not data:
            return self.create_empty_chart()

        fig = go.Figure()

        for idx, workflow in enumerate(WORKFLOWS):
            if workflow not in data:
                continue

            df = pd.DataFrame(data[workflow])
            if df.empty:
                continue

            weekly_stats = self.prepare_weekly_data(df)
            weekly_stats["success_rate"] = self.calculate_success_rate(weekly_stats)
            weekly_stats["week_end"] = weekly_stats.index + pd.Timedelta(days=6)

            hover_text = [
                f"{format_workflow_name(workflow)}<br>"
                f"{start.strftime('%d.%m')} - {end.strftime('%d.%m')}<br>"
                f"Success Rate: {success_rate:.2f}%"
                for start, end, success_rate in zip(
                    weekly_stats.index, weekly_stats["week_end"], weekly_stats["success_rate"]
                )
            ]

            fig.add_trace(
                go.Scatter(
                    x=weekly_stats.index,
                    y=weekly_stats["success_rate"],
                    mode="lines+markers",
                    name=format_workflow_name(workflow),
                    marker=dict(symbol=self.marker_symbols[idx % len(self.marker_symbols)]),
                    hovertext=hover_text,
                    hoverinfo="text",
                )
            )

        fig.update_layout(
            title="Weekly Success Rate",
            xaxis_title="Week End",
            yaxis_title="Success Rate (%)",
            legend_title="Workflow",
            hovermode="x unified",
        )

        return fig
