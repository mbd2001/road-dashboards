from typing import override

import pandas as pd
from road_database_toolkit.databases.workflows.workflow_enums import WorkflowType

from road_dashboards.workflows_dashboard.common.analytics import analytics_manager
from road_dashboards.workflows_dashboard.common.consts import ComponentIds
from road_dashboards.workflows_dashboard.components.base.pie_chart import PieChart


class ErrorPieChart(PieChart):
    def __init__(self, workflow_type: WorkflowType):
        super().__init__(f"{ComponentIds.ERROR_PIE_CHART}-{workflow_type.value}", workflow_type)

    @override
    def get_chart_title(self) -> str:
        return "Error Distribution"

    @override
    def get_hover_template(self) -> str:
        return "<b>Error Message:</b><br>%{customdata}<br><br>Count: %{value}<br>%{percent}<extra></extra>"

    @override
    def get_chart_data(
        self, brain_types: list[str], start_date: str | None, end_date: str | None, selected_workflow
    ) -> pd.DataFrame:
        if selected_workflow != self.workflow_type.value:
            return pd.DataFrame()

        return analytics_manager.get_error_distribution(self.workflow_type, brain_types, start_date, end_date)

    @override
    def get_chart_params(self) -> dict:
        params = super().get_chart_params()
        params["custom_data"] = ["full_message"]
        return params
