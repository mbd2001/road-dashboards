import pandas as pd
from road_database_toolkit.dynamo_db.db_manager import DBManager

from workflows_dashboard.config import DBConfig, WorkflowFields


class WorkflowsDBManager(DBManager):
    def __init__(self):
        super().__init__(table_name=DBConfig.table_name, primary_key=DBConfig.primary_key)

    def get_all_workflow_data(self) -> pd.DataFrame:
        """Get all workflow data as a DataFrame."""
        items = self.table.scan().get("Items", [])
        if not items:
            return pd.DataFrame()

        df = pd.DataFrame(items)
        df["workflows"] = df["workflows"].apply(list)

        return df

    def _process_workflow_df(
        self, df: pd.DataFrame, workflow_name: str, brains: list = None, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Process workflow DataFrame with filtering and column renaming."""
        if df.empty:
            return pd.DataFrame()

        filtered_df = df[df["workflows"].apply(lambda x: workflow_name in x)].copy()

        if brains:
            filtered_df = filtered_df[filtered_df[WorkflowFields.brain_type].isin(brains)]

        if start_date or end_date:
            last_update_col = f"{workflow_name}_last_update"
            filtered_df[last_update_col] = pd.to_datetime(filtered_df[last_update_col])

            if start_date:
                start_date = pd.to_datetime(start_date)
                filtered_df = filtered_df[filtered_df[last_update_col] >= start_date]

            if end_date:
                end_date = pd.to_datetime(end_date)
                filtered_df = filtered_df[filtered_df[last_update_col] <= end_date]

        # Rename columns by removing workflow_name prefix
        workflow_prefix = f"{workflow_name}_"
        column_mapping = {col: col.replace(workflow_prefix, "") for col in filtered_df.columns}

        return filtered_df.rename(columns=column_mapping)

    def get_multiple_workflow_data(
        self, workflows: list, brains: list = None, start_date: str = None, end_date: str = None
    ) -> dict:
        """Get data for multiple workflows with optional filtering."""
        all_data = self.get_all_workflow_data()
        workflow_data = {}

        for workflow in workflows:
            workflow_data[workflow] = self._process_workflow_df(all_data, workflow, brains, start_date, end_date)

        return workflow_data
