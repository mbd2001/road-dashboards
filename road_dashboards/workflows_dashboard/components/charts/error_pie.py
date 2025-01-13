from typing import override

import pandas as pd

from road_dashboards.workflows_dashboard.components.base.pie_chart import PieChart
from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds
from road_dashboards.workflows_dashboard.database.workflow_manager import db_manager


class ErrorPieChart(PieChart):
    def __init__(self, workflow_name: str):
        super().__init__(f"{ComponentIds.ERROR_PIE_CHART}-{workflow_name}", workflow_name)

    def get_chart_title(self) -> str:
        return "Error Distribution"

    def get_hover_template(self) -> str:
        return "<b>Error Message:</b><br>%{customdata}<br><br>Count: %{value}<br>%{percent}<extra></extra>"

    @override
    def get_chart_data(
        self, brain_types: list[str], start_date: str | None, end_date: str | None, selected_workflow
    ) -> pd.DataFrame:
        if selected_workflow != self.workflow_name:
            return pd.DataFrame()

        return db_manager.get_error_distribution(self.workflow_name, brain_types, start_date, end_date)

    def get_chart_params(self) -> dict:
        params = super().get_chart_params()
        params["custom_data"] = ["full_message"]
        return params
