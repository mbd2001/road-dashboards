from textwrap import wrap
from typing import Dict, List, Optional, Tuple

import pandas as pd

from road_dashboards.workflows_dashboard.components.base.pie_chart import BasePieChart
from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds, Status
from road_dashboards.workflows_dashboard.core_settings.settings import ChartSettings


class ErrorPieChart(BasePieChart):
    def __init__(self, workflow_name: str, max_segments: int = 10):
        super().__init__(f"{ComponentIds.ERROR_PIE_CHART}-{workflow_name}", workflow_name)
        self.max_segments = max_segments

    @staticmethod
    def truncate_error_message(message: str) -> str:
        """Truncate error message to a maximum length."""
        message = message.replace("\n", " ")
        if len(message) > ChartSettings.max_error_message_length:
            return message[: ChartSettings.max_error_message_length] + "..."
        return message.ljust(ChartSettings.max_error_message_length)

    def get_failed_entries(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Extract failed entries from the dataframe."""
        if df.empty:
            return None

        failed_df = df[df["status"] == Status.FAILED.value]
        return failed_df if not failed_df.empty else None

    def create_message_mapping(self, failed_df: pd.DataFrame) -> Tuple[Dict[str, str], pd.Series]:
        """Create mapping between truncated and full messages and get error counts."""
        failed_df = failed_df.copy()
        failed_df["truncated_message"] = failed_df["message"].apply(self.truncate_error_message)

        message_mapping = dict(zip(failed_df["truncated_message"], failed_df["message"]))
        error_counts = failed_df["truncated_message"].value_counts()

        return message_mapping, error_counts

    def group_less_frequent_errors(
        self, error_counts: pd.Series, message_mapping: Dict[str, str]
    ) -> Tuple[List[int], List[str], List[str]]:
        """Group less frequent errors into 'Others' category if needed."""
        if len(error_counts) <= self.max_segments:
            return (
                list(error_counts.values),
                list(error_counts.index),
                [message_mapping[name] for name in error_counts.index],
            )

        top_errors = error_counts.nlargest(self.max_segments - 1)
        others_count = error_counts[self.max_segments - 1 :].sum()

        counts = list(top_errors.values) + [others_count]
        messages = list(top_errors.index) + ["Others"]
        full_messages = [message_mapping[name] for name in top_errors.index] + ["Various other errors"]

        return counts, messages, full_messages

    def prepare_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Prepare data for visualization."""
        failed_df = self.get_failed_entries(df)
        if failed_df is None:
            return None

        message_mapping, error_counts = self.create_message_mapping(failed_df)
        counts, messages, full_messages = self.group_less_frequent_errors(error_counts, message_mapping)

        return pd.DataFrame({"count": counts, "message": messages, "full_message": full_messages})

    def get_chart_title(self) -> str:
        return "Error Distribution"

    def get_hover_template(self) -> str:
        return "<b>Error Message:</b><br>%{customdata[0]}<br><br>Count: %{value}<br>%{percent}<extra></extra>"

    def get_chart_params(self) -> dict:
        return {"custom_data": ["full_message"]}
