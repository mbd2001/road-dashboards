from abc import abstractmethod
from typing import Any, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from road_dashboards.workflows_dashboard.components.base.chart import Chart
from road_dashboards.workflows_dashboard.utils.chart_utils import add_center_annotation


class PieChart(Chart):
    def __init__(self, chart_id: str, workflow_name: str):
        super().__init__(chart_id)
        self.workflow_name = workflow_name

    @abstractmethod
    def get_chart_title(self) -> str:
        """Get the chart title."""
        pass

    @abstractmethod
    def get_hover_template(self) -> str:
        """Get the hover template for the chart."""
        pass

    def get_chart_params(self) -> Dict[str, Any]:
        """Get additional chart parameters."""
        return {}

    def create_chart(
        self,
        data: pd.DataFrame,
    ) -> go.Figure:
        """
        Create a pie chart based on the provided data.

        Args:
            data: DataFrame with 'message' and 'count' columns

        Returns:
            go.Figure: A plotly pie chart figure
        """
        total_count = data["count"].sum()
        chart_params = self.get_chart_params()

        fig = px.pie(data, values="count", names="message", title=self.get_chart_title(), **chart_params)

        add_center_annotation(fig, f"Total Clips:<br><b>{total_count}</b>")
        self._update_traces(fig)

        return fig

    def _update_traces(self, fig: px.pie) -> None:
        """Update the traces with consistent styling."""
        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            insidetextfont=dict(size=10),
            hovertemplate=self.get_hover_template(),
        )
        fig.update_layout(
            hoverlabel=dict(
                font_size=10,
                namelength=-1,
            )
        )
