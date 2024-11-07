from abc import abstractmethod
from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px

from workflows_dashboard.components.base.base_chart import BaseChart
from workflows_dashboard.utils.chart_utils import add_center_annotation


class BasePieChart(BaseChart):
    def __init__(self, chart_id: str, workflow_name: str):
        super().__init__(chart_id)
        self.workflow_name = workflow_name

    @abstractmethod
    def prepare_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Prepare data for visualization."""
        pass

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

    def create_chart(self, df: pd.DataFrame) -> px.pie:
        plot_df = self.prepare_data(df)
        if plot_df is None:
            return self.create_empty_chart()

        total_count = plot_df["count"].sum()
        chart_params = self.get_chart_params()

        fig = px.pie(plot_df, values="count", names="message", title=self.get_chart_title(), **chart_params)

        add_center_annotation(fig, f"Total Clips:<br><b>{total_count}</b>")

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

        return fig
