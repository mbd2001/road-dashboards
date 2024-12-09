from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from boto3.dynamodb.conditions import Attr
from road_database_toolkit.dynamo_db.db_manager import DBManager

from road_dashboards.workflows_dashboard.core_settings.constants import WORKFLOWS, WorkflowFields
from road_dashboards.workflows_dashboard.core_settings.settings import ChartSettings, DatabaseSettings, Status


class WorkflowsDBManager(DBManager):
    def __init__(self):
        super().__init__(table_name=DatabaseSettings.table_name, primary_key=DatabaseSettings.primary_key)
        self._workflow_dfs: dict[str, pd.DataFrame] = {}
        self._load_workflow_data()

    def _load_workflow_data(self) -> None:
        """Loads all data as df for each workflow."""

        def fetch_workflow_data(workflow: str) -> tuple[str, pd.DataFrame]:
            """Helper function to fetch data for a single workflow."""
            filter_expr = Attr("workflows").contains(workflow)
            projection_expr = (
                f"#pk, brain_type, {workflow}_{WorkflowFields.status}, {workflow}_{WorkflowFields.message}, "
                f"{workflow}_{WorkflowFields.last_update}, {workflow}_{WorkflowFields.job_id}, {workflow}_{WorkflowFields.exit_code}"
            )
            expr_names = {"#pk": DatabaseSettings.primary_key}

            items = []
            total_segments = 4

            with ThreadPoolExecutor(max_workers=total_segments) as executor:
                futures = []
                for segment in range(total_segments):
                    future = executor.submit(
                        self.scan,
                        FilterExpression=filter_expr,
                        ProjectionExpression=projection_expr,
                        ExpressionAttributeNames=expr_names,
                        Segment=segment,
                        TotalSegments=total_segments,
                    )
                    futures.append(future)

                for future in futures:
                    items.extend(future.result())

            return workflow, pd.DataFrame(items) if items else pd.DataFrame()

        with ThreadPoolExecutor() as executor:  # One thread per workflow
            results = list(executor.map(fetch_workflow_data, WORKFLOWS))

        for workflow, df in results:
            if df.empty:
                continue

            column_mapping = {
                f"{workflow}_{WorkflowFields.status}": WorkflowFields.status,
                f"{workflow}_{WorkflowFields.message}": WorkflowFields.message,
                f"{workflow}_{WorkflowFields.last_update}": WorkflowFields.last_update,
            }

            for col in [WorkflowFields.job_id, WorkflowFields.exit_code]:
                if col in df.columns:
                    column_mapping[col] = f"{workflow}_{col}"

            df = df.rename(columns=column_mapping)
            df[WorkflowFields.last_update] = pd.to_datetime(df[WorkflowFields.last_update])
            df[WorkflowFields.status] = df[WorkflowFields.status].fillna(Status.UNPROCESSED.value)

            self._workflow_dfs[workflow] = df

    def _get_filtered_df(
        self, workflow_name: str = None, brain_types=None, start_date=None, end_date=None, statuses=None
    ) -> pd.DataFrame:
        """
        Get filtered DataFrame based on common filters.

        Args:
            workflow_name (str, optional): Name of specific workflow to filter
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering in ISO format
            end_date (str, optional): End date for filtering in ISO format
            statuses (list[str], optional): List of statuses to filter by

        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        if not workflow_name:
            return pd.DataFrame()

        df = self._workflow_dfs.get(workflow_name, pd.DataFrame())
        if df.empty:
            return df

        if brain_types:
            df = df[df[WorkflowFields.brain_type].isin(brain_types)]
        if start_date:
            df = df[df[WorkflowFields.last_update] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df[WorkflowFields.last_update] <= pd.to_datetime(end_date)]
        if statuses:
            df = df[df[WorkflowFields.status].isin(statuses)]

        return df

    def get_status_distribution(
        self, workflow_name: str, brain_types=None, start_date=None, end_date=None
    ) -> pd.DataFrame:
        """
        Get status distribution for a specific workflow.

        Args:
            workflow_name (str): Name of the workflow
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering in ISO format
            end_date (str, optional): End date for filtering in ISO format

        Returns:
            pd.DataFrame: DataFrame with status counts
                         Columns: ['message', 'count']
                         Example:
                         message      | count
                         'SUCCESS'    | 42
                         'FAILED'     | 12
                         'IN_PROGRESS'| 5
        """
        filtered_df = self._get_filtered_df(workflow_name, brain_types, start_date, end_date)
        if filtered_df.empty:
            return pd.DataFrame(columns=["message", "count"])

        status_counts = filtered_df[WorkflowFields.status].value_counts()
        return pd.DataFrame({"message": status_counts.index, "count": status_counts.values})

    def get_error_distribution(
        self, workflow_name: str, brain_types=None, start_date=None, end_date=None
    ) -> pd.DataFrame:
        """
        Get error distribution for failed cases.

        Args:
            workflow_name (str): Name of the workflow
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering in ISO format
            end_date (str, optional): End date for filtering in ISO format

        Returns:
            pd.DataFrame: DataFrame with error message counts
                         Columns: ['message', 'count']
                         Example:
                         message                  | count
                         'Connection timeout'     | 15
                         'Invalid input format'   | 8
        """
        filtered_df = self._get_filtered_df(workflow_name, brain_types, start_date, end_date)
        if filtered_df.empty:
            return pd.DataFrame(columns=["message", "count"])

        error_df = filtered_df[filtered_df[WorkflowFields.status] == Status.FAILED]
        error_counts = error_df[WorkflowFields.message].value_counts()

        error_counts.index = [
            f"{x[:ChartSettings.max_error_message_length]}..." if len(x) > ChartSettings.max_error_message_length else x
            for x in error_counts.index
        ]

        return pd.DataFrame({"message": error_counts.index, "count": error_counts.values})

    def get_weekly_success_data(self, brain_types=None, start_date=None, end_date=None) -> pd.DataFrame:
        """
        Get weekly success rate data for all workflows.

        Args:
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering in ISO format
            end_date (str, optional): End date for filtering in ISO format

        Returns:
            pd.DataFrame: DataFrame with columns:
                - week_start: Week start date
                - workflow: Workflow name
                - success_count: Number of successful runs
                - failed_count: Number of failed runs
                - success_rate: Success rate as percentage
        """
        result_data = []
        statuses = [Status.SUCCESS.value, Status.FAILED.value]
        for workflow_name in self._workflow_dfs:
            filtered_df = self._get_filtered_df(workflow_name, brain_types, start_date, end_date, statuses)
            if filtered_df.empty:
                continue

            weekly_stats = (
                filtered_df.groupby(
                    [
                        pd.Grouper(key=WorkflowFields.last_update, freq="W-SUN", closed="left", label="left"),
                        WorkflowFields.status,
                    ]
                )
                .size()
                .unstack(fill_value=0)
            )

            for status in [Status.SUCCESS, Status.FAILED]:
                if status not in weekly_stats.columns:
                    weekly_stats[status] = 0

            total_count = weekly_stats[Status.SUCCESS] + weekly_stats[Status.FAILED]
            success_rate = (weekly_stats[Status.SUCCESS.value] / total_count * 100).fillna(0)

            for week_start, row in weekly_stats.iterrows():
                result_data.append(
                    {
                        "week_start": week_start,
                        "workflow": workflow_name,
                        "success_count": row[Status.SUCCESS.value],
                        "failed_count": row[Status.FAILED.value],
                        "success_rate": success_rate[week_start],
                    }
                )

        return pd.DataFrame(result_data)

    def get_workflow_export_data(
        self, workflows: list[str], brain_types=None, start_date=None, end_date=None
    ) -> pd.DataFrame:
        """
        Get specific workflow data for export.

        Args:
            workflows (list[str]): List of workflow names to export
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering in ISO format
            end_date (str, optional): End date for filtering in ISO format

        Returns:
            pd.DataFrame: DataFrame containing workflow data with columns for each workflow
        """
        if not workflows:
            return pd.DataFrame()

        result_df = None

        for workflow in workflows:
            filtered_df = self._get_filtered_df(workflow, brain_types, start_date, end_date)
            if filtered_df.empty:
                continue

            column_mapping = {
                WorkflowFields.status: f"{workflow}_{WorkflowFields.status}",
                WorkflowFields.message: f"{workflow}_{WorkflowFields.message}",
                WorkflowFields.last_update: f"{workflow}_{WorkflowFields.last_update}",
            }
            for col in [WorkflowFields.job_id, WorkflowFields.exit_code]:
                if col in filtered_df.columns:
                    column_mapping[col] = f"{workflow}_{col}"

            filtered_df = filtered_df.rename(columns=column_mapping)

            if result_df is None:
                result_df = filtered_df
            else:
                result_df = pd.merge(
                    result_df, filtered_df, on=[DatabaseSettings.primary_key, "brain_type"], how="outer"
                )

        if result_df is None:
            return pd.DataFrame()

        columns = [DatabaseSettings.primary_key, "brain_type"]
        other_columns = [col for col in result_df.columns if col not in columns]
        result_df = result_df[columns + other_columns]

        return result_df


db_manager = WorkflowsDBManager()
