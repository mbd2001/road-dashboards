from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional, Dict, List, Tuple, Any

import pandas as pd
from boto3.dynamodb.conditions import Attr
from road_database_toolkit.dynamo_db.db_manager import DBManager

from road_dashboards.workflows_dashboard.core_settings.constants import BRAIN_OPTIONS, WORKFLOWS, WorkflowFields
from road_dashboards.workflows_dashboard.core_settings.settings import ChartSettings, DatabaseSettings, Status

TOTAL_SCAN_SEGMENTS = 4
MAX_WORKERS_PER_WORKFLOW = 4
CACHE_EXPIRATION_HOURS = 24


class WorkflowsDBManager(DBManager):
    """Manages workflow data from DynamoDB, providing methods for data analysis and visualization."""

    def __init__(self) -> None:
        """Initialize the WorkflowsDBManager with DynamoDB connection and load workflow data."""
        super().__init__(table_name=DatabaseSettings.table_name, primary_key=DatabaseSettings.primary_key)
        self._workflow_dfs: Dict[str, pd.DataFrame] = {}
        self._last_refresh: Optional[datetime] = None
        self._refresh_lock = Lock()
        self._load_workflow_data()

    def _should_refresh_data(self) -> bool:
        """
        Check if data should be refreshed based on cache expiration time.

        Returns:
            bool: True if data should be refreshed, False otherwise
        """
        if self._last_refresh is None:
            return True
        
        time_since_refresh = datetime.now() - self._last_refresh
        return time_since_refresh > timedelta(hours=CACHE_EXPIRATION_HOURS)

    def _ensure_fresh_data(self) -> None:
        """
        Ensure data is fresh by checking cache expiration and refreshing if needed.
        Thread-safe implementation using a lock.
        """
        if not self._should_refresh_data():
            return

        with self._refresh_lock:
            self._load_workflow_data()
            self._last_refresh = datetime.now()

    def _load_workflow_data(self) -> None:
        """
        Loads and preprocesses workflow data from DynamoDB into DataFrames.
        Uses parallel processing for efficient data loading.
        """
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(self._fetch_workflow_data, WORKFLOWS))

        self._workflow_dfs.clear()  # Clear existing data before updating
        for workflow, df in results:
            if df.empty:
                continue

            df = self._remove_workflow_prefix_mapping(workflow, df)
            df[WorkflowFields.last_update] = pd.to_datetime(df[WorkflowFields.last_update])
            df[WorkflowFields.status] = df[WorkflowFields.status].fillna(Status.UNPROCESSED.value)
            self._workflow_dfs[workflow] = df

    def _fetch_workflow_data(self, workflow: str) -> Tuple[str, pd.DataFrame]:
        """
        Fetches data for a single workflow using parallel scanning.

        Args:
            workflow: Name of the workflow to fetch data for

        Returns:
            Tuple of workflow name and corresponding DataFrame
        """
        filter_expr = Attr("workflows").contains(workflow)
        projection_expr = self._build_projection_expression(workflow)
        expr_names = {"#pk": DatabaseSettings.primary_key}

        items = []
        with ThreadPoolExecutor(max_workers=TOTAL_SCAN_SEGMENTS) as executor:
            futures = [
                executor.submit(
                    self.scan,
                    FilterExpression=filter_expr,
                    ProjectionExpression=projection_expr,
                    ExpressionAttributeNames=expr_names,
                    Segment=segment,
                    TotalSegments=TOTAL_SCAN_SEGMENTS,
                )
                for segment in range(TOTAL_SCAN_SEGMENTS)
            ]
            for future in futures:
                items.extend(future.result())

        return workflow, pd.DataFrame(items) if items else pd.DataFrame()

    @staticmethod
    def _build_projection_expression(workflow: str) -> str:
        """
        Builds the projection expression for DynamoDB query.

        Args:
            workflow: Name of the workflow

        Returns:
            Projection expression string
        """
        return (
            f"#pk, brain_type, {workflow}_{WorkflowFields.status}, {workflow}_{WorkflowFields.message}, "
            f"{workflow}_{WorkflowFields.last_update}, {workflow}_{WorkflowFields.job_id}, "
            f"{workflow}_{WorkflowFields.exit_code}, {workflow}_{WorkflowFields.jira_key}"
        )

    def _get_filtered_df(
        self,
        workflow_name: Optional[str] = None,
        brain_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        allowed_values_per_column: Optional[Dict[str, List[str]]] = None,
    ) -> pd.DataFrame:
        """
        Get filtered DataFrame based on common filters.

        Args:
            workflow_name: Name of specific workflow to filter
            brain_types: List of brain types to filter by
            start_date: Start date for filtering in ISO format
            end_date: End date for filtering in ISO format
            statuses: List of statuses to filter by
            allowed_values_per_column: Dictionary mapping column names to list of allowed values

        Returns:
            Filtered DataFrame
        """
        # self._ensure_fresh_data()  # Ensure data is fresh before filtering

        if not workflow_name:
            return pd.DataFrame()

        df = self._workflow_dfs.get(workflow_name, pd.DataFrame())
        if df.empty:
            return df

        # Apply filters sequentially
        if brain_types:
            df = df[df[WorkflowFields.brain_type].isin(brain_types)]
        if start_date:
            df = df[df[WorkflowFields.last_update] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df[WorkflowFields.last_update] <= pd.to_datetime(end_date)]
        if statuses:
            df = df[df[WorkflowFields.status].isin(statuses)]
        if allowed_values_per_column:
            for col, values in allowed_values_per_column.items():
                df = df[df[col].astype(str).isin(values)]

        return df

    def get_status_distribution(
        self,
        workflow_name: str,
        brain_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get status distribution for a specific workflow.

        Args:
            workflow_name: Name of the workflow
            brain_types: List of brain types to filter by
            start_date: Start date for filtering in ISO format
            end_date: End date for filtering in ISO format

        Returns:
            DataFrame with status counts and messages
            Columns: ['message', 'count']
        """
        filtered_df = self._get_filtered_df(workflow_name, brain_types, start_date, end_date)
        if filtered_df.empty:
            return pd.DataFrame(columns=["message", "count"])

        status_counts = filtered_df[WorkflowFields.status].value_counts()
        return pd.DataFrame({"message": status_counts.index, "count": status_counts.values})

    def get_error_distribution(
        self,
        workflow_name: str,
        brain_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get error distribution for failed cases.

        Args:
            workflow_name: Name of the workflow
            brain_types: List of brain types to filter by
            start_date: Start date for filtering in ISO format
            end_date: End date for filtering in ISO format

        Returns:
            DataFrame with error message counts
            Columns: ['message', 'count']
        """
        filtered_df = self._get_filtered_df(workflow_name, brain_types, start_date, end_date)
        if filtered_df.empty:
            return pd.DataFrame(columns=["message", "count"])

        error_df = filtered_df[filtered_df[WorkflowFields.status] == Status.FAILED]
        error_counts = error_df[WorkflowFields.message].value_counts()

        cleaned_messages = [message.replace("Error: ", "") for message in error_counts.index]

        def truncate_message(message: str) -> str:
            if len(message) > ChartSettings.max_error_message_length:
                return f"{message[:ChartSettings.max_error_message_length]}..."
            return message

        truncated_messages = [truncate_message(x) for x in cleaned_messages]
            
        return pd.DataFrame({
            "message": truncated_messages,
            "full_message": cleaned_messages,
            "count": error_counts.values
        })

    def get_weekly_success_data(
        self,
        brain_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get weekly success rate data for all workflows.

        Args:
            brain_types: List of brain types to filter by
            start_date: Start date for filtering in ISO format
            end_date: End date for filtering in ISO format

        Returns:
            DataFrame with weekly success metrics
            Columns: ['week_start', 'workflow', 'success_count', 'failed_count', 'success_rate']
        """
        result_data = []
        statuses = [Status.SUCCESS.value, Status.FAILED.value]

        for workflow_name in self._workflow_dfs:
            filtered_df = self._get_filtered_df(workflow_name, brain_types, start_date, end_date, statuses)
            if filtered_df.empty:
                continue

            weekly_stats = self._calculate_weekly_stats(filtered_df)
            result_data.extend(self._format_weekly_stats(workflow_name, weekly_stats))

        return pd.DataFrame(result_data)

    def _calculate_weekly_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate weekly statistics for a workflow DataFrame.

        Args:
            df: Input DataFrame with workflow data

        Returns:
            DataFrame with weekly statistics
        """
        return (
            df.groupby(
                [
                    pd.Grouper(key=WorkflowFields.last_update, freq="W-SUN", closed="left", label="left"),
                    WorkflowFields.status,
                ]
            )
            .size()
            .unstack(fill_value=0)
        )

    def _format_weekly_stats(self, workflow_name: str, weekly_stats: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Format weekly statistics into a list of dictionaries.

        Args:
            workflow_name: Name of the workflow
            weekly_stats: DataFrame with weekly statistics

        Returns:
            List of dictionaries with formatted weekly statistics
        """
        result = []
        
        # Ensure success and failed columns exist
        for status in [Status.SUCCESS, Status.FAILED]:
            if status not in weekly_stats.columns:
                weekly_stats[status] = 0

        total_count = weekly_stats[Status.SUCCESS] + weekly_stats[Status.FAILED]
        success_rate = (weekly_stats[Status.SUCCESS.value] / total_count * 100).fillna(0)

        for week_start, row in weekly_stats.iterrows():
            result.append({
                "week_start": week_start,
                "workflow": workflow_name,
                "success_count": row[Status.SUCCESS.value],
                "failed_count": row[Status.FAILED.value],
                "success_rate": success_rate[week_start],
            })

        return result

    def _add_workflow_prefix_mapping(self, workflow: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add workflow prefix to column names in DataFrame.

        Args:
            workflow: Name of the workflow
            df: Input DataFrame

        Returns:
            DataFrame with workflow-prefixed column names
        """
        non_workflow_columns = [DatabaseSettings.primary_key, WorkflowFields.brain_type]
        return df.rename(columns=lambda col: f"{workflow}_{col}" if col not in non_workflow_columns else col)

    def _remove_workflow_prefix_mapping(self, workflow: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove workflow prefix from column names in DataFrame.

        Args:
            workflow: Name of the workflow
            df: Input DataFrame

        Returns:
            DataFrame with workflow prefix removed from column names
        """
        return df.rename(columns=lambda col: col.replace(f"{workflow}_", ""))

    def get_workflow_export_data(
        self,
        workflows: List[str],
        brain_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        allowed_values_per_column: Optional[Dict[str, List[str]]] = None,
    ) -> pd.DataFrame:
        """
        Get specific workflow data for export.

        Args:
            workflows: List of workflow names to export
            brain_types: List of brain types to filter by
            start_date: Start date for filtering in ISO format
            end_date: End date for filtering in ISO format
            statuses: List of statuses to filter by
            allowed_values_per_column: Dictionary of column filters

        Returns:
            DataFrame containing workflow data with columns for each workflow
        """
        if not workflows:
            return pd.DataFrame()

        merge_keys = [DatabaseSettings.primary_key, WorkflowFields.brain_type]

        result_df = pd.DataFrame(columns=merge_keys)
        
        for workflow in workflows:
            filtered_df = self._get_filtered_df(workflow, brain_types, start_date, end_date, statuses, allowed_values_per_column)
            if filtered_df.empty:
                continue

            # Add workflow prefix if exporting multiple workflows
            if len(workflows) > 1: 
                filtered_df = self._add_workflow_prefix_mapping(workflow, filtered_df)

            result_df = pd.merge(result_df, filtered_df, on=merge_keys, how="outer")

        non_key_columns = [col for col in result_df.columns if col not in merge_keys]
 
        return result_df[merge_keys + non_key_columns]

    def get_workflow_success_count_data(
        self,
        brain_types: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get the success count for each workflow and brain type combination.

        Args:
            brain_types: List of brain types to filter by
            start_date: Start date to filter by
            end_date: End date to filter by

        Returns:
            DataFrame with workflow and brain type success count data
            Columns: ['workflow', 'brain_type', 'success_count']
        """
        success_data = []
        brain_types = brain_types or BRAIN_OPTIONS

        for workflow in WORKFLOWS:
            success_df = self._get_filtered_df(
                workflow_name=workflow,
                brain_types=brain_types,
                start_date=start_date,
                end_date=end_date,
                statuses=[Status.SUCCESS.value],
            )

            if success_df.empty:
                success_data.extend([
                    {"workflow": workflow, "brain_type": brain, "success_count": 0}
                    for brain in brain_types
                ])
                continue


            for brain_type in brain_types:
                brain_success_df = success_df[success_df[WorkflowFields.brain_type] == brain_type]
                success_data.append({
                    "workflow": workflow,
                    "brain_type": brain_type,
                    "success_count": len(brain_success_df)
                })

        return pd.DataFrame(success_data)

    def get_workflow_columns(self, workflow_name: str) -> List[str]:
        """
        Get list of columns for a specific workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            List of column names
        """
        df = self._workflow_dfs.get(workflow_name, pd.DataFrame())
        return list(df.columns)

    def get_unique_column_values(
        self,
        workflow_name: str,
        column_name: str,
        brain_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        allowed_values_per_column: Optional[Dict[str, List[str]]] = None,
    ) -> List[str]:
        """
        Get unique values for a specific column in a workflow.

        Args:
            workflow_name: Name of the workflow
            column_name: Name of the column
            brain_types: List of brain types to filter by
            start_date: Start date for filtering in ISO format
            end_date: End date for filtering in ISO format
            statuses: List of statuses to filter by
            allowed_values_per_column: Dictionary of column filters

        Returns:
            List of unique values in the column, sorted
        """
        filtered_df = self._get_filtered_df(
            workflow_name=workflow_name,
            brain_types=brain_types,
            start_date=start_date,
            end_date=end_date,
            statuses=statuses,
            allowed_values_per_column=allowed_values_per_column,
        )

        if filtered_df.empty or column_name not in filtered_df.columns:
            return []

        values = filtered_df[column_name].dropna().unique()
        if pd.api.types.is_numeric_dtype(values):
            return [str(x) for x in sorted(values.astype(int))]
        else:
            return sorted(values.astype(str).tolist())


db_manager = WorkflowsDBManager()
