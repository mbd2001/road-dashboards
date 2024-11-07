from datetime import datetime

import pandas as pd
from loguru import logger
from road_database_toolkit.dynamo_db.db_manager import DBManager

from workflows_dashboard.core_settings.constants import WORKFLOWS, WorkflowFields
from workflows_dashboard.core_settings.settings import DatabaseSettings


class WorkflowsDBManager(DBManager):
    """
    Manages workflow data retrieval and caching from DynamoDB.

    This class extends DBManager to provide specialized functionality for workflow data,
    including caching, pagination, and filtering capabilities.
    """

    def __init__(self):
        super().__init__(table_name=DatabaseSettings.table_name, primary_key=DatabaseSettings.primary_key)
        self._cached_data = None
        self._last_fetch_time = None

    def get_all_workflow_data(self, brain_types=None, start_date=None, end_date=None) -> dict:
        """
        Retrieves and filters workflow data from cache or database.

        Args:
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering results
            end_date (str, optional): End date for filtering results

        Returns:
            dict: Dictionary mapping workflow names to their filtered records
        """
        if self._should_refresh_cache():
            self._cached_data = self._fetch_all_data()

        return self._filter_cached_data(brain_types, start_date, end_date)

    def _should_refresh_cache(self) -> bool:
        if not self._last_fetch_time:
            return True
        cache_age = datetime.now() - self._last_fetch_time
        return cache_age.total_seconds() > 300  # 5 minutes

    def _fetch_all_data(self) -> pd.DataFrame:
        """
        Fetches all workflow data from DynamoDB using pagination.

        Returns:
            pd.DataFrame: DataFrame containing all workflow records
        """
        all_items = []
        last_evaluated_key = None

        while True:
            response = self.get_paginated_workflow_data(page_size=1000, last_evaluated_key=last_evaluated_key)

            items = response["items"]
            all_items.extend(items)

            last_evaluated_key = response["last_evaluated_key"]
            if not last_evaluated_key:  # No more pages
                break

        if not all_items:
            return pd.DataFrame()

        df = pd.DataFrame(all_items)
        df["workflows"] = df["workflows"].apply(list)
        self._last_fetch_time = datetime.now()
        return df

    def _filter_cached_data(self, brain_types, start_date, end_date) -> dict:
        """
        Filters cached workflow data based on specified criteria.

        Args:
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering results
            end_date (str, optional): End date for filtering results

        Returns:
            dict: Dictionary mapping workflow names to their filtered records
        """
        if self._cached_data is None or self._cached_data.empty:
            return {workflow: [] for workflow in WORKFLOWS}

        workflow_data = {}
        for workflow in WORKFLOWS:
            workflow_records = self._process_workflow_df(
                self._cached_data.copy(), workflow, brain_types, start_date, end_date
            )

            if not workflow_records.empty:
                if "workflows" in workflow_records.columns:
                    workflow_records = workflow_records.drop("workflows", axis=1)
                workflow_data[workflow] = workflow_records.to_dict("records")
            else:
                workflow_data[workflow] = []

        return workflow_data

    def _process_workflow_df(
        self, df: pd.DataFrame, workflow_name: str, brain_types=None, start_date=None, end_date=None
    ) -> pd.DataFrame:
        """
        Processes and filters workflow DataFrame based on specified criteria.

        Args:
            df (pd.DataFrame): Input DataFrame containing workflow data
            workflow_name (str): Name of the workflow to process
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering results
            end_date (str, optional): End date for filtering results

        Returns:
            pd.DataFrame: Filtered and processed DataFrame with only relevant columns
        """
        if df.empty:
            return pd.DataFrame()

        filtered_df = df[df["workflows"].apply(lambda x: workflow_name in x)].copy()

        if brain_types:
            filtered_df = filtered_df[filtered_df[WorkflowFields.brain_type].isin(brain_types)]

        prefix = f"{workflow_name}_"
        workflow_cols = [col for col in filtered_df.columns if col.startswith(prefix)]
        cols_to_keep = workflow_cols + [WorkflowFields.clip_name, WorkflowFields.brain_type]
        filtered_df = filtered_df[cols_to_keep]

        renamed_columns = {col: col.replace(prefix, "") for col in workflow_cols}
        filtered_df = filtered_df.rename(columns=renamed_columns)

        if WorkflowFields.last_update in filtered_df.columns:
            if start_date:
                filtered_df = filtered_df[filtered_df[WorkflowFields.last_update] >= start_date]
            if end_date:
                filtered_df = filtered_df[filtered_df[WorkflowFields.last_update] <= end_date]

        return filtered_df

    def get_paginated_workflow_data(self, page_size: int = 1000, last_evaluated_key: dict = None):
        """
        Retrieves a paginated set of workflow data from DynamoDB.

        Args:
            page_size (int, optional): Number of records to retrieve per page. Defaults to 1000.
            last_evaluated_key (dict, optional): Key for pagination continuation

        Returns:
            dict: Dictionary containing:
                - items: List of workflow records
                - last_evaluated_key: Key for retrieving the next page of results
        """
        scan_kwargs = {"Limit": page_size}
        if last_evaluated_key:
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        response = self.table.scan(**scan_kwargs)
        return {"items": response.get("Items", []), "last_evaluated_key": response.get("LastEvaluatedKey")}
