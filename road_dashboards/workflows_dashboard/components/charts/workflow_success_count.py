import pandas as pd
import plotly.graph_objects as go
from typing_extensions import override

from road_dashboards.workflows_dashboard.components.base.chart import Chart
from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds
from road_dashboards.workflows_dashboard.database.workflow_manager import db_manager
from road_dashboards.workflows_dashboard.utils.chart_utils import BAR_CHART_COLORS
from road_dashboards.workflows_dashboard.utils.formatting import format_workflow_name


class WorkflowSuccessCountChart(Chart):
    def __init__(self):
        super().__init__(ComponentIds.WORKFLOW_SUCCESS_COUNT_CHART)

    @override
    def create_chart(
        self,
        data: pd.DataFrame,
    ) -> go.Figure:
        """
        Create a workflow success count chart with separate bars for each brain type.

        Args:
            data: DataFrame containing workflow success count data

        Returns:
            go.Figure: A plotly figure object
        """
        fig = go.Figure()

        # Get unique brain types and workflows
        brain_types = data["brain_type"].unique()
        workflows = data["workflow"].unique()

        # Create a bar for each brain type within each workflow
        for idx, brain_type in enumerate(brain_types):
            brain_data = data[data["brain_type"] == brain_type]

            fig.add_trace(
                go.Bar(
                    name=brain_type,
                    x=[format_workflow_name(w) for w in workflows],
                    y=brain_data["success_count"],
                    marker_color=BAR_CHART_COLORS[idx % len(BAR_CHART_COLORS)],
                    text=brain_data["success_count"],
                    textposition="auto",
                    hovertemplate=f"{brain_type}<br>Success Count: %{{y}}<extra></extra>",
                )
            )

        self._update_layout(fig)
        return fig

    def _update_layout(self, fig):
        fig.update_layout(
            title="Workflow Success Count by Brain Type",
            xaxis_title="Workflow",
            yaxis_title="Number of Succeeded Clips",
            barmode="group",
            bargap=0.15,
            bargroupgap=0.1,
            showlegend=True,
            plot_bgcolor="white",
            xaxis=dict(showgrid=False, showline=True, linecolor="lightgray"),
            yaxis=dict(showgrid=True, gridcolor="lightgray", showline=True, linecolor="lightgray"),
        )

    @override
    def get_chart_data(
        self,
        brain_types: list[str],
        start_date: str | None,
        end_date: str | None,
        selected_workflow: str,
    ) -> pd.DataFrame:
        return db_manager.get_workflow_success_count_data(
            brain_types=brain_types,
            start_date=start_date,
            end_date=end_date,
        )
