from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from boto3.dynamodb.conditions import Attr
from road_database_toolkit.dynamo_db.db_manager import DBManager

from road_dashboards.workflows_dashboard.core_settings.constants import BRAIN_OPTIONS, WORKFLOWS, WorkflowFields
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
                f"{workflow}_{WorkflowFields.last_update}, {workflow}_{WorkflowFields.job_id}, {workflow}_{WorkflowFields.exit_code}, {workflow}_{WorkflowFields.jira_key}"
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

            df = self._remove_workflow_prefix_mapping(workflow, df)

            df[WorkflowFields.last_update] = pd.to_datetime(df[WorkflowFields.last_update])
            df[WorkflowFields.status] = df[WorkflowFields.status].fillna(Status.UNPROCESSED.value)

            self._workflow_dfs[workflow] = df

    def _get_filtered_df(
        self,
        workflow_name: str = None,
        brain_types=None,
        start_date=None,
        end_date=None,
        statuses=None,
        column_filters=None,
    ) -> pd.DataFrame:
        """
        Get filtered DataFrame based on common filters.

        Args:
            workflow_name (str, optional): Name of specific workflow to filter
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering in ISO format
            end_date (str, optional): End date for filtering in ISO format
            statuses (list[str], optional): List of statuses to filter by
            column_filters (dict, optional): Dictionary of column filters in the format:
                {column_name: list_of_values}
                Example: {"exit_code": ["0", "1"]}

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

        if column_filters:
            for col, values in column_filters.items():
                if col in df.columns and values:
                    df = df[df[col].astype(str).isin(values)]

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

    def _add_workflow_prefix_mapping(self, workflow: str, df: pd.DataFrame) -> dict:
        """Get column mapping for workflow DataFrame.

        Args:
            workflow: Name of the workflow
            df: DataFrame containing workflow data

        Returns:
            Dictionary mapping original column names to workflow-specific names
        """
        non_workflow_columns = [DatabaseSettings.primary_key, WorkflowFields.brain_type]
        return df.rename(columns=lambda col: f"{workflow}_{col}" if col not in non_workflow_columns else col)

    def _remove_workflow_prefix_mapping(self, workflow: str, df: pd.DataFrame) -> pd.DataFrame:
        """Remove workflow-specific prefix from column names.

        Args:
            workflow: Name of the workflow
            df: DataFrame containing workflow data

        Returns:
            DataFrame with column names without workflow-specific prefix
        """

        return df.rename(columns=lambda col: col.replace(f"{workflow}_", ""))

    def get_workflow_export_data(
        self, workflows: list[str], brain_types=None, start_date=None, end_date=None, statuses=None, column_filters=None
    ) -> pd.DataFrame:
        """
        Get specific workflow data for export.

        Args:
            workflows (list[str]): List of workflow names to export
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering in ISO format
            end_date (str, optional): End date for filtering in ISO format
            statuses (list[str], optional): List of statuses to filter by
            column_filters (dict, optional): Dictionary of column filters in the format:
                {column_name: list_of_values}
                Example: {"exit_code": ["0", "1"]}

        Returns:
            pd.DataFrame: DataFrame containing workflow data with columns for each workflow
        """
        if not workflows:
            return pd.DataFrame()

        merge_keys = [DatabaseSettings.primary_key, WorkflowFields.brain_type]

        # For single workflow export, don't add workflow prefix
        if len(workflows) == 1:
            workflow = workflows[0]
            filtered_df = self._get_filtered_df(workflow, brain_types, start_date, end_date, statuses, column_filters)
            if filtered_df.empty:
                return pd.DataFrame()
            filtered_df = filtered_df[merge_keys + [col for col in filtered_df.columns if col not in merge_keys]]
            return filtered_df

        # For multiple workflows, add prefix to distinguish between workflows
        result_df = None

        for workflow in workflows:
            filtered_df = self._get_filtered_df(workflow, brain_types, start_date, end_date, statuses, column_filters)
            if filtered_df.empty:
                continue

            filtered_df = self._add_workflow_prefix_mapping(workflow, filtered_df)

            if result_df is None:
                result_df = filtered_df
            else:
                result_df = pd.merge(result_df, filtered_df, on=merge_keys, how="outer")

        if result_df is None:
            return pd.DataFrame()

        result_df = result_df[merge_keys + [col for col in result_df.columns if col not in merge_keys]]
        return result_df

    def get_workflow_success_count_data(
        self,
        brain_types: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        Get the success count for each workflow and brain type combination.

        Args:
            brain_types: List of brain types to filter by
            start_date: Optional start date to filter by
            end_date: Optional end date to filter by

        Returns:
            DataFrame with workflow and brain type success count data
        """
        success_data = []

        for workflow in WORKFLOWS:
            total_df = self._get_filtered_df(
                workflow_name=workflow,
                brain_types=brain_types,
                start_date=start_date,
                end_date=end_date,
                statuses=[Status.SUCCESS.value, Status.FAILED.value],
            )

            if total_df.empty:
                for brain in brain_types:
                    success_data.append({"workflow": workflow, "brain_type": brain, "success_count": 0})
                continue

            success_df = total_df[total_df[WorkflowFields.status] == Status.SUCCESS.value]

            if brain_types is None or len(brain_types) == 0:
                brain_types = BRAIN_OPTIONS

            for brain_type in brain_types:
                brain_success_df = success_df[success_df[WorkflowFields.brain_type] == brain_type]
                brain_success = len(brain_success_df)

                success_data.append({"workflow": workflow, "brain_type": brain_type, "success_count": brain_success})

        return pd.DataFrame(success_data)

    def get_workflow_columns(self, workflow_name: str) -> list[str]:
        df = self._workflow_dfs.get(workflow_name, pd.DataFrame())
        return list(df.columns)

    def get_unique_column_values(
        self,
        workflow_name: str,
        column_name: str,
        brain_types=None,
        start_date=None,
        end_date=None,
        statuses=None,
        column_filters=None,
    ) -> list:
        """
        Get unique values for a specific column in a workflow.

        Args:
            workflow_name (str): Name of the workflow
            column_name (str): Name of the column
            brain_types (list[str], optional): List of brain types to filter by
            start_date (str, optional): Start date for filtering in ISO format
            end_date (str, optional): End date for filtering in ISO format
            statuses (list[str], optional): List of statuses to filter by
            column_filters (dict, optional): Dictionary of column filters

        Returns:
            list: List of unique values in the column, sorted
        """
        filtered_df = self._get_filtered_df(
            workflow_name=workflow_name,
            brain_types=brain_types,
            start_date=start_date,
            end_date=end_date,
            statuses=statuses,
            column_filters=column_filters,
        )

        if filtered_df.empty or column_name not in filtered_df.columns:
            return []

        values = filtered_df[column_name].dropna().unique()
        try:
            return [str(x) for x in sorted(values.astype(int))]
        except:
            return sorted(values.astype(str).tolist())


db_manager = WorkflowsDBManager()
