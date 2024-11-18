from typing import Optional

import pandas as pd

from road_dashboards.workflows_dashboard.components.base.pie_chart import BasePieChart
from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds
from road_dashboards.workflows_dashboard.core_settings.settings import ChartSettings
from road_dashboards.workflows_dashboard.database.workflow_manager import WorkflowsDBManager


class StatusPieChart(BasePieChart):
    def __init__(self, workflow_name: str):
        super().__init__(f"{ComponentIds.STATUS_PIE_CHART}-{workflow_name}", workflow_name)
        self.db_manager = WorkflowsDBManager()

    def prepare_data(self, filters: dict) -> Optional[pd.DataFrame]:
        df = self.db_manager.get_status_distribution(
            self.workflow_name,
            brain_types=filters.get("brain_types"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
        )

        if df.empty:
            return None

        if "message" not in df.columns or "count" not in df.columns:
            return None

        return df

    def get_chart_title(self) -> str:
        return "Status Distribution"

    def get_hover_template(self) -> str:
        return "%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"

    def get_chart_params(self) -> dict:
        return {"color_discrete_map": ChartSettings.default_colors, "color": "message"}
