from textwrap import wrap
from typing import Dict, List, Optional, Tuple

import pandas as pd

from road_dashboards.workflows_dashboard.components.base.pie_chart import BasePieChart
from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds, Status
from road_dashboards.workflows_dashboard.core_settings.settings import ChartSettings
from road_dashboards.workflows_dashboard.database.workflow_manager import WorkflowsDBManager


class ErrorPieChart(BasePieChart):
    def __init__(self, workflow_name: str):
        super().__init__(f"{ComponentIds.ERROR_PIE_CHART}-{workflow_name}", workflow_name)
        self.db_manager = WorkflowsDBManager()

    def prepare_data(self, filters: dict) -> Optional[pd.DataFrame]:
        df = self.db_manager.get_error_distribution(
            self.workflow_name,
            brain_types=filters.get("brain_types"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
        )

        if df.empty:
            return None

        if "message" not in df.columns or "count" not in df.columns:
            return None

        max_length = ChartSettings.max_error_message_length
        df["message"] = df["message"].apply(lambda x: f"{x[:max_length]}..." if len(x) > max_length else x)

        return df

    def get_chart_title(self) -> str:
        return "Error Distribution"

    def get_hover_template(self) -> str:
        return "<b>Error Message:</b><br>%{label}<br><br>Count: %{value}<br>%{percent}<extra></extra>"
