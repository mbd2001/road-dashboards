from typing import Optional

import pandas as pd

from road_dashboards.workflows_dashboard.components.base.pie_chart import BasePieChart
from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds
from road_dashboards.workflows_dashboard.core_settings.settings import ChartSettings


class StatusPieChart(BasePieChart):
    def __init__(self, workflow_name: str):
        super().__init__(f"{ComponentIds.STATUS_PIE_CHART}-{workflow_name}", workflow_name)

    def prepare_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        if df.empty:
            return None

        status_counts = df["status"].value_counts()
        return pd.DataFrame({"count": status_counts.values, "message": status_counts.index})

    def get_chart_title(self) -> str:
        return "Status Distribution"

    def get_hover_template(self) -> str:
        return "%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"

    def get_chart_params(self) -> dict:
        return {"color_discrete_map": ChartSettings.default_colors, "color": "message"}
