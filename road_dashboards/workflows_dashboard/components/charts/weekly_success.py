from typing import override

import pandas as pd
import plotly.graph_objects as go

from road_dashboards.workflows_dashboard.common.analytics import analytics_manager
from road_dashboards.workflows_dashboard.common.config import ChartSettings
from road_dashboards.workflows_dashboard.common.consts import ComponentIds
from road_dashboards.workflows_dashboard.common.utils import format_workflow_type
from road_dashboards.workflows_dashboard.components.base.chart import Chart


class WeeklySuccessChart(Chart):
    def __init__(self):
        super().__init__(ComponentIds.WEEKLY_SUCCESS_RATE_CHART)
        self.marker_symbols = ChartSettings.marker_symbols

    def create_chart(
        self,
        data: pd.DataFrame,
    ) -> go.Figure:
        """
        Create a weekly success rate chart.

        Args:
            data: DataFrame containing weekly success rate data

        Returns:
            go.Figure: A plotly figure object
        """
        fig = go.Figure()

        for idx, (workflow, workflow_data) in enumerate(data.groupby("workflow")):
            self._add_workflow_trace(fig, workflow, workflow_data, idx)

        self._update_layout(fig)
        return fig

    def _add_workflow_trace(self, fig, workflow, workflow_data, idx):
        hover_text = [
            f"{format_workflow_type(workflow)}<br>"
            f"{start.strftime('%d.%m')} - {(start + pd.Timedelta(days=6)).strftime('%d.%m')}<br>"
            f"Success Rate: {rate:.2f}% ({success_count}/{success_count + failed_count})"
            for start, rate, success_count, failed_count in zip(
                workflow_data["week_start"],
                workflow_data["success_rate"],
                workflow_data["success_count"],
                workflow_data["failed_count"],
            )
        ]

        fig.add_trace(
            go.Scatter(
                x=workflow_data["week_start"],
                y=workflow_data["success_rate"],
                mode="lines+markers",
                name=format_workflow_type(workflow),
                marker=dict(symbol=self.marker_symbols[idx % len(self.marker_symbols)]),
                text=hover_text,
                hoverinfo="text",
                hovertemplate="%{text}<extra></extra>",
            )
        )

    def _update_layout(self, fig):
        fig.update_layout(
            title="Weekly Success Rate",
            xaxis_title="Week Start",
            yaxis_title="Success Rate (%)",
            legend_title="Workflow",
            hovermode="x",
            hoverdistance=1,
        )

    @override
    def get_chart_data(
        self,
        brain_types: list[str],
        start_date: str | None,
        end_date: str | None,
        selected_workflow: str,
    ) -> pd.DataFrame:
        return analytics_manager.get_weekly_success_data(
            brain_types=brain_types,
            start_date=start_date,
            end_date=end_date,
        )
