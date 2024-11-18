import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback

from road_dashboards.workflows_dashboard.components.base.chart import BaseChart
from road_dashboards.workflows_dashboard.core_settings.constants import WORKFLOWS, ComponentIds, Status
from road_dashboards.workflows_dashboard.core_settings.settings import ChartSettings
from road_dashboards.workflows_dashboard.database.workflow_manager import WorkflowsDBManager
from road_dashboards.workflows_dashboard.utils.formatting import format_workflow_name


class WeeklySuccessChart(BaseChart):
    def __init__(self):
        super().__init__(ComponentIds.WEEKLY_SUCCESS_RATE_CHART)
        self.marker_symbols = ChartSettings.marker_symbols
        self.db_manager = WorkflowsDBManager()

    def create_chart(self, filters: dict) -> go.Figure:
        """
        Create a weekly success rate chart.

        Args:
            filters (dict): Filter parameters from BaseChart.create_chart

        Returns:
            go.Figure: Line chart showing success rates over time for each workflow
        """
        weekly_data = self.db_manager.get_weekly_success_data(
            brain_types=filters.get("brain_types"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
        )

        if not weekly_data:
            return self.create_empty_chart()

        fig = go.Figure()
        for idx, (workflow, stats) in enumerate(weekly_data.items()):
            if len(stats["week_start"]) == 0:
                continue

            self._add_workflow_trace(fig, workflow, stats, idx)

        self._update_layout(fig)
        return fig

    def _add_workflow_trace(self, fig, workflow, stats, idx):
        hover_text = [
            f"{format_workflow_name(workflow)}<br>"
            f"{start.strftime('%d.%m')} - {(start + pd.Timedelta(days=6)).strftime('%d.%m')}<br>"
            f"Success Rate: {rate:.2f}%"
            for start, rate in zip(stats["week_start"], stats["success_rate"])
        ]

        fig.add_trace(
            go.Scatter(
                x=stats["week_start"],
                y=stats["success_rate"],
                mode="lines+markers",
                name=format_workflow_name(workflow),
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
