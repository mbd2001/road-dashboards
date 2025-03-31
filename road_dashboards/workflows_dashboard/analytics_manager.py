from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import Lock
from typing import Any, Iterable

import pandas as pd
from loguru import logger
from road_database_toolkit.databases.workflows.config import workflows_config
from road_database_toolkit.databases.workflows.models import Clip, WorkflowRun
from road_database_toolkit.databases.workflows.workflow_enums import (
    BrainType,
    Status,
    WorkflowRunFields,
    WorkflowRunSpecificColumns,
    WorkflowType,
)
from road_database_toolkit.postgresql.db_manager import PostgresConfig, get_session
from road_database_toolkit.utils.cache import hashable_lru_cache
from sqlalchemy import DateTime, desc, distinct, func, select

MAX_CACHE_SIZE = 100
EXPIRATION_TIME = timedelta(minutes=30)
MAX_ERROR_MSG_LENGTH = 50


WORKFLOW_SPECIFIC_COLUMNS_MAP = {
    WorkflowType.DV: [WorkflowRunSpecificColumns.job_id, WorkflowRunSpecificColumns.exit_code],
    WorkflowType.EMDP: [WorkflowRunSpecificColumns.job_id, WorkflowRunSpecificColumns.exit_code],
    WorkflowType.GTRM: [WorkflowRunSpecificColumns.jira_key],
    WorkflowType.PANOPTIC: [WorkflowRunSpecificColumns.jira_key],
}


class AnalyticsManager:
    """
    Analytics-focused database manager for workflow data visualization.
    Provides efficient read-only queries for statistics and reporting with caching.
    """

    def __init__(self) -> None:
        """Initialize the AnalyticsManager with cache management."""
        self._cache_lock = Lock()
        self._last_refresh: datetime | None = None
        self.db_config: PostgresConfig = workflows_config

    def _build_base_select(self, select_columns: list[Any], join_clip_table: bool = False) -> Any:
        """Constructs a base SQLAlchemy 2.0 select statement.

        Args:
            select_columns: List of columns/entities to select.
            join_clip_table: Whether to join the Clip table with Workflow table.

        Returns:
            SQLAlchemy select statement.
        """
        stmt = select(*select_columns)
        if join_clip_table:
            stmt = stmt.join(Clip, WorkflowRun.clip_name == Clip.clip_name)
        return stmt

    def _apply_common_filters(
        self,
        stmt: Any,  # select() statement
        workflow_type: WorkflowType | None = None,
        brain_types: Iterable[BrainType] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        statuses: Iterable[Status] | None = None,
    ) -> Any:
        """Applies common filters using .where() clauses."""
        conditions = []
        if workflow_type:
            conditions.append(WorkflowRun.workflow_type == workflow_type)

        if brain_types:
            conditions.append(Clip.brain_type.in_(brain_types))

        if statuses:
            conditions.append(WorkflowRun.status.in_(statuses))

        if start_date:
            start_datetime = pd.to_datetime(start_date, utc=True).to_pydatetime(warn=False)
            conditions.append(WorkflowRun.updated_at >= start_datetime)

        if end_date:
            end_datetime = pd.to_datetime(end_date, utc=True).to_pydatetime(warn=False)
            conditions.append(WorkflowRun.updated_at <= end_datetime)

        if conditions:
            stmt = stmt.where(*conditions)
        return stmt

    def _should_refresh_cache(self) -> bool:
        if self._last_refresh is None:
            return True
        now = datetime.now(timezone.utc if self._last_refresh.tzinfo else None)
        return (now - self._last_refresh) > EXPIRATION_TIME

    def refresh_data(self) -> None:
        with self._cache_lock:
            methods = [
                self.get_status_distribution,
                self.get_error_distribution,
                self.get_weekly_success_data,
                self.get_workflow_success_count_data,
                self.get_unique_column_values,
                self.get_unique_status_values,
            ]

            for method in methods:
                try:
                    method.cache_clear()
                except Exception as e:
                    logger.warning(f"Failed to clear cache for {method.__name__}: {e}")
            self._last_refresh = datetime.now(timezone.utc)

    def _ensure_fresh_cache(self) -> None:
        """Ensure cache is fresh, refreshing if needed."""
        if self._should_refresh_cache():
            self.refresh_data()

    @hashable_lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_status_distribution(
        self,
        workflow_type: WorkflowType,
        brain_types: tuple[BrainType, ...] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        self._ensure_fresh_cache()
        join_clip = brain_types is not None

        with get_session(self.db_config) as session:
            stmt = self._build_base_select(
                select_columns=[WorkflowRun.status, func.count(WorkflowRun.id).label("count")],
                join_clip_table=join_clip,
            )
            stmt = self._apply_common_filters(
                stmt, workflow_type=workflow_type, brain_types=brain_types, start_date=start_date, end_date=end_date
            )
            stmt = stmt.group_by(WorkflowRun.status)
            results = session.execute(stmt).all()

            if not results:
                return pd.DataFrame(columns=["message", "count"])

            data = [
                {"message": result.status.value if result.status else None, "count": result.count} for result in results
            ]
            return pd.DataFrame(data)

    def get_specific_workflow_columns(self, workflow_type: WorkflowType) -> tuple[WorkflowRunSpecificColumns, ...]:
        """
        Get specific workflow columns that are applicable for the given workflow type.
        """
        assert workflow_type in WORKFLOW_SPECIFIC_COLUMNS_MAP, (
            f"Workflow type {workflow_type} is not supported. Please add it accordingly."
        )
        return WORKFLOW_SPECIFIC_COLUMNS_MAP[workflow_type]

    @hashable_lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_error_distribution(
        self,
        workflow_type: WorkflowType,
        brain_types: tuple[BrainType, ...] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        top_n: int = 10,
    ) -> pd.DataFrame:
        self._ensure_fresh_cache()
        join_clip = brain_types is not None

        with get_session(self.db_config) as session:
            stmt = self._build_base_select(
                select_columns=[WorkflowRun.message, func.count(WorkflowRun.id).label("count")],
                join_clip_table=join_clip,
            )
            stmt = self._apply_common_filters(
                stmt,
                workflow_type=workflow_type,
                brain_types=brain_types,
                start_date=start_date,
                end_date=end_date,
                statuses=(Status.FAILED,),
            )
            stmt = stmt.where(WorkflowRun.message.isnot(None))
            stmt = stmt.group_by(WorkflowRun.message).order_by(desc("count"))

            results = session.execute(stmt).all()

            if not results:
                return pd.DataFrame(columns=["message", "count", "full_message"])

            messages, full_messages, counts = [], [], []
            other_count = 0
            for i, result in enumerate(results):
                if i < top_n:
                    clean_message = result.message.replace("Error: ", "")
                    full_messages.append(clean_message)
                    truncated = (
                        clean_message[:MAX_ERROR_MSG_LENGTH] + "..."
                        if len(clean_message) > MAX_ERROR_MSG_LENGTH
                        else clean_message
                    )
                    messages.append(truncated)
                    counts.append(result.count)
                else:
                    other_count += result.count

            if other_count > 0:
                messages.append("Other")
                full_messages.append("Aggregated count of less frequent errors")
                counts.append(other_count)

            return pd.DataFrame({"message": messages, "count": counts, "full_message": full_messages})

    @hashable_lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_weekly_success_data(
        self,
        brain_types: tuple[BrainType, ...] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        self._ensure_fresh_cache()
        if not end_date:
            end_dt = datetime.now(timezone.utc)
            end_date = end_dt.isoformat()

        end_dt = pd.to_datetime(end_date, utc=True).to_pydatetime(warn=False)

        if not start_date:
            start_dt = end_dt - timedelta(days=90)
            start_date = start_dt.isoformat()
        else:
            start_dt = pd.to_datetime(start_date, utc=True).to_pydatetime(warn=False)

        with get_session(self.db_config) as session:
            week_start_col = func.date_trunc("week", WorkflowRun.updated_at, type_=DateTime(timezone=True)).label(
                "week_start"
            )
            join_clip = brain_types is not None

            stmt = select(
                week_start_col, WorkflowRun.workflow_type, WorkflowRun.status, func.count(WorkflowRun.id).label("count")
            )
            if join_clip:
                stmt = stmt.join(Clip, WorkflowRun.clip_name == Clip.clip_name)

            stmt = self._apply_common_filters(
                stmt,
                brain_types=brain_types,
                start_date=start_date,
                end_date=end_date,
                statuses=(Status.SUCCESS, Status.FAILED),
            )
            stmt = stmt.group_by(week_start_col, WorkflowRun.workflow_type, WorkflowRun.status)
            stmt = stmt.order_by(week_start_col, WorkflowRun.workflow_type)

            results = session.execute(stmt).all()

            if not results:
                return pd.DataFrame(columns=["week_start", "workflow", "success_count", "failed_count", "success_rate"])

            df = pd.DataFrame(results, columns=["week_start", "workflow", "status", "count"])
            pivot_df = df.pivot_table(
                index=["week_start", "workflow"], columns="status", values="count", fill_value=0
            ).reset_index()

            if Status.SUCCESS not in pivot_df.columns:
                pivot_df[Status.SUCCESS] = 0
            if Status.FAILED not in pivot_df.columns:
                pivot_df[Status.FAILED] = 0

            pivot_df.rename(columns={Status.SUCCESS: "success_count", Status.FAILED: "failed_count"}, inplace=True)

            total = pivot_df["success_count"] + pivot_df["failed_count"]
            pivot_df["success_rate"] = (pivot_df["success_count"] / total * 100).fillna(0)
            pivot_df["workflow"] = pivot_df["workflow"].apply(lambda x: x.value if isinstance(x, Enum) else x)

            return pivot_df[["week_start", "workflow", "success_count", "failed_count", "success_rate"]]

    def _build_export_select(
        self,
        workflow_type: WorkflowType,
        brain_types: Iterable[BrainType] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        statuses: Iterable[Status] | None = None,
        allowed_values_per_column: dict[str, Iterable[str]] | None = None,
        limit: int = 1000,
    ) -> Any:
        """Builds the select statement for exporting workflow data."""
        stmt = select(Clip, WorkflowRun).join(WorkflowRun, Clip.clip_name == WorkflowRun.clip_name)

        stmt = self._apply_common_filters(
            stmt,
            workflow_type=workflow_type,
            brain_types=brain_types,
            start_date=start_date,
            end_date=end_date,
            statuses=statuses,
        )

        if allowed_values_per_column:
            for column, values in allowed_values_per_column.items():
                if not values:
                    continue
                column_attr = getattr(WorkflowRun, column, None)
                if column_attr is not None:
                    stmt = stmt.where(column_attr.in_(values))
                else:
                    raise ValueError(f"Invalid column name for filtering: {column}")

        stmt = stmt.order_by(desc(WorkflowRun.updated_at)).limit(limit)
        return stmt

    def _process_export_row(self, clip: Clip, workflow_run: WorkflowRun, workflow_type: WorkflowType) -> dict[str, Any]:
        """Processes a (Clip, Workflow) row for export."""
        workflow_specific_columns = self.get_specific_workflow_columns(workflow_type)
        row = {
            WorkflowRunFields.clip_name: clip.clip_name,
            WorkflowRunFields.brain_type: clip.brain_type.value if clip.brain_type else None,
            WorkflowRunFields.status: workflow_run.status.value if workflow_run.status else None,
            WorkflowRunFields.message: workflow_run.message,
            WorkflowRunFields.updated_at: workflow_run.updated_at.isoformat() if workflow_run.updated_at else None,
            WorkflowRunFields.created_at: workflow_run.created_at.isoformat() if workflow_run.created_at else None,
            **{col: getattr(workflow_run, col, None) for col in workflow_specific_columns},
        }
        if isinstance(workflow_run.workflow_metadata, dict):
            meta_flat = {f"meta_{k}": v for k, v in workflow_run.workflow_metadata.items()}
            row.update(meta_flat)
        return row

    def get_workflow_export_data(
        self,
        workflows: tuple[str, ...],
        brain_types: tuple[BrainType, ...] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        statuses: tuple[Status, ...] | None = None,
        allowed_values_per_column: dict[str, tuple[str, ...]] | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        if not workflows:
            return pd.DataFrame()

        result_dfs = []
        with get_session(self.db_config) as session:
            for workflow_type in workflows:
                stmt = self._build_export_select(
                    workflow_type, brain_types, start_date, end_date, statuses, allowed_values_per_column, limit
                )
                results = session.execute(stmt).all()
                if not results:
                    continue

                data = [self._process_export_row(clip, wf, workflow_type) for clip, wf in results]
                df = pd.DataFrame(data)

                if len(workflows) > 1:
                    df = self._add_workflow_prefix(workflow_type, df)
                result_dfs.append(df)

        if not result_dfs:
            return pd.DataFrame()
        if len(result_dfs) == 1:
            return result_dfs[0]

        merged_df = result_dfs[0]
        merge_keys = [WorkflowRunFields.clip_name, WorkflowRunFields.brain_type]

        for df_to_merge in result_dfs[1:]:
            current_merge_keys = [k for k in merge_keys if k in df_to_merge.columns]
            merged_df = pd.merge(merged_df, df_to_merge, on=current_merge_keys, how="outer")

        return merged_df

    def _add_workflow_prefix(self, workflow: str, df: pd.DataFrame) -> pd.DataFrame:
        """Adds workflow prefix to columns, except common keys."""
        no_prefix_columns = [WorkflowRunFields.clip_name, WorkflowRunFields.brain_type]
        rename_dict = {col: f"{workflow}_{col}" for col in df.columns if col not in no_prefix_columns}
        return df.rename(columns=rename_dict)

    @hashable_lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_workflow_success_count_data(
        self,
        brain_types: tuple[BrainType, ...] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        self._ensure_fresh_cache()
        with get_session(self.db_config) as session:
            stmt = select(
                WorkflowRun.workflow_type, Clip.brain_type, func.count(WorkflowRun.id).label("success_count")
            ).join(Clip, WorkflowRun.clip_name == Clip.clip_name)

            stmt = self._apply_common_filters(
                stmt, brain_types=brain_types, start_date=start_date, end_date=end_date, statuses=(Status.SUCCESS,)
            )
            stmt = stmt.group_by(WorkflowRun.workflow_type, Clip.brain_type)
            results = session.execute(stmt).all()

            if not results:
                return pd.DataFrame(columns=["workflow", "brain_type", "success_count"])

            data = [
                {
                    "workflow": result.workflow_type.value if result.workflow_type else None,
                    "brain_type": result.brain_type.value if result.brain_type else None,
                    "success_count": result.success_count,
                }
                for result in results
            ]
            return pd.DataFrame(data)

    @hashable_lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_unique_status_values(
        self,
        workflow_type: WorkflowType,
        brain_types: tuple[BrainType, ...] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[Status]:
        self._ensure_fresh_cache()
        join_clip = brain_types is not None

        with get_session(self.db_config) as session:
            stmt = select(distinct(WorkflowRun.status))
            if join_clip:
                stmt = stmt.join(Clip, WorkflowRun.clip_name == Clip.clip_name)

            stmt = self._apply_common_filters(
                stmt, workflow_type=workflow_type, brain_types=brain_types, start_date=start_date, end_date=end_date
            )
            stmt = stmt.where(WorkflowRun.status.isnot(None))
            results = session.scalars(stmt).all()
            return results

    @hashable_lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_unique_column_values(
        self,
        workflow_type: WorkflowType,
        column_name: str,
        brain_types: tuple[BrainType, ...] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        statuses: tuple[Status, ...] | None = None,
        filter_column_values: dict[str, Iterable[str]] | None = None,
    ) -> list[str]:
        """
        Get unique values for a specified column from the Workflow table.

        Args:
            workflow_type: The type of workflow to filter by.
            column_name: The name of the column to get unique values for.
            brain_types: The brain types to filter by.
            start_date: The start date to filter by.
            end_date: The end date to filter by.
            statuses: The statuses to filter by.
            filter_column_values: A dictionary of column names and values to filter by.

        Returns:
            A list of unique values for the specified column.
        """
        self._ensure_fresh_cache()

        target_column_attr = getattr(WorkflowRun, column_name, None)
        if target_column_attr is None:
            raise ValueError(f"Invalid column name specified: {column_name}")

        with get_session(self.db_config) as session:
            stmt = select(distinct(target_column_attr))
            join_clip = brain_types is not None

            stmt = self._apply_common_filters(
                stmt,
                workflow_type=workflow_type,
                brain_types=brain_types,
                start_date=start_date,
                end_date=end_date,
                statuses=statuses,
            )

            if filter_column_values:
                for col, values in filter_column_values.items():
                    if not values:
                        continue
                    col_attr = getattr(WorkflowRun, col, None)
                    if col_attr is None:
                        col_attr = getattr(Clip, col, None)

                    if col_attr is not None:
                        stmt = stmt.where(col_attr.in_(values))
                    else:
                        raise ValueError(f"Invalid column name in filter_column_values: {col}")

            stmt = stmt.where(target_column_attr.isnot(None))
            results = session.scalars(stmt).all()
            if isinstance(target_column_attr.type, Enum):
                return [r.value for r in results]
            return results
