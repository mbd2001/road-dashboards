from dataclasses import dataclass, field
from typing import List

import pandas as pd
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import BASE_COLUMNS, Case, Column
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import Table

BASE_COLUMNS = [Column(col) for col in BASE_COLUMNS]


SELECT_QUERY = """
    (SELECT {columns_to_select} 
    FROM {main_data} A {unnest_arrays}
    {filters})
    """

JOIN_QUERY = """
    (SELECT {columns_to_select} 
    FROM {main_data} A {unnest_arrays} INNER JOIN {secondary_data} B
    ON ((A.clip_name = B.clip_name) AND (A.grabindex = B.grabindex)) 
    {filters})
    """

WITH_QUERY = """
    WITH {base_name} AS 
    ({query})
    {to_select}
    """

DIFF_IDS_QUERY = """
    SELECT A.clip_name, A.grabindex
    FROM ({main_data}) A INNER JOIN ({secondary_data}) B
    ON ((A.clip_name = B.clip_name) AND (A.grabindex = B.grabindex) AND (A.obj_id = B.obj_id))
    WHERE A.{column_to_compare} != B.{column_to_compare}
    GROUP BY A.clip_name, A.grabindex   
    LIMIT {limit}
    """

DIFF_LABELS_QUERY = """
    WITH t1 AS (
        {diff_ids_query}
    )
    SELECT t2.clip_name, t2.grabindex, t2.dump_name, {agg_columns}
    FROM (SELECT clip_name, grabindex, dump_name, {label_columns} FROM {main_data} UNION ALL SELECT clip_name, grabindex, dump_name, {label_columns} FROM {secondary_data}) t2
    INNER JOIN t1 ON t1.clip_name = t2.clip_name AND t1.grabindex = t2.grabindex
    GROUP BY t2.clip_name, t2.grabindex, t2.dump_name
    """

CONF_QUERY = """
    SELECT main_val, secondary_val, COUNT(*) AS overall FROM (
        SELECT A.{column_to_compare} AS main_val, B.{column_to_compare} AS secondary_val
        FROM ({main_data}) A INNER JOIN ({secondary_data}) B
        ON ((A.clip_name = B.clip_name) AND (A.grabindex = B.grabindex) AND (A.obj_id = B.obj_id))
    )
    GROUP BY main_val, secondary_val
    """


COUNT_QUERY = """
    SELECT dump_name {group_by} {group_name}, {metric}
    FROM (
        {sub_query}
    )
    GROUP BY dump_name {group_by} ORDER BY dump_name
    """

CASES_DESCRIPTION = """
    SELECT *,
    CASE
        {cases}
        ELSE 'other'
    END AS {output_name}
    FROM (
        {sub_query}
    )
    """

COUNT_PERCENTAGE = """
    WITH t1 AS (
        {query}
    )
    SELECT dump_name {group_by}, (100.0 * overall) / (SUM(overall) OVER (PARTITION BY dump_name)) as percentage
    FROM t1
    """

IMG_LIMIT = 25


@dataclass(kw_only=True)
class Metric:
    output_name: str

    def get_metric(self) -> str:
        raise NotImplementedError


@dataclass
class CountMetric(Metric):
    output_name: str = "overall"
    filter: str = "*"
    format_number: bool = False

    def get_metric(self) -> str:
        metric = f"COUNT({self.filter})"
        metric = f"format_number({metric})" if self.format_number else metric
        return f"{metric} AS {self.output_name}"


@dataclass
class Query:
    def get_query(self) -> str:
        raise NotImplementedError

    def get_results(self) -> pd.DataFrame:
        data, _ = query_athena(database="run_eval_db", query=self.get_query())
        return data


@dataclass
class BaseDataQuery(Query):
    """
    Defines the base properties of a query

    extra_columns (list): the columns included in the interesting cases
    ignore_filter (str): optional. which rows to ignore when computing the query. can be turned off by the user
    """

    main_tables: List[Table]
    meta_data_tables: List[Table] = None
    data_filter: str = None
    page_filters: str = ""
    dumps_to_include: List[str] = None
    intersection_on: bool = False
    extra_columns: List[Column] = field(default_factory=list)

    def get_query(
        self,
    ) -> str:
        main_paths = self.filter_paths(self.main_tables, self.dumps_to_include)
        meta_data_paths = (
            self.filter_paths(self.meta_data_tables, self.dumps_to_include) if self.meta_data_tables else None
        )
        filters = self.generate_filters(self.data_filter, self.page_filters, main_paths, self.intersection_on)
        base_data = self.generate_base_data(main_paths, filters, meta_data_paths, self.extra_columns)
        return base_data

    @staticmethod
    def generate_base_data(
        main_paths: List[str], filters: str, meta_data_paths: List[str] = None, extra_columns: List[Column] = None
    ):
        reg_columns = [col for col in extra_columns if not getattr(col, "unnest", False)]
        columns_to_unnest = [col for col in extra_columns if getattr(col, "unnest", False)]

        select_columns = ", ".join(
            [col.get_column_as_original_name() for col in set(BASE_COLUMNS + reg_columns)]
            + [f"T.{col.name}" for col in columns_to_unnest]
        )
        unnest_arrays = ", ".join(f"{col.get_column_string()} AS T({col.name})" for col in columns_to_unnest)
        unnest_arrays = f"CROSS JOIN {unnest_arrays}" if unnest_arrays else ""
        if meta_data_paths:
            datasets_list = [
                JOIN_QUERY.format(
                    columns_to_select=select_columns,
                    main_data=main_table,
                    unnest_arrays=unnest_arrays,
                    secondary_data=md_table,
                    filters=filters,
                )
                for main_table, md_table in zip(main_paths, meta_data_paths)
                if main_table
            ]
        else:
            datasets_list = [
                SELECT_QUERY.format(
                    columns_to_select=select_columns,
                    main_data=main_table,
                    unnest_arrays=unnest_arrays,
                    filters=filters,
                )
                for main_table in main_paths
                if main_table
            ]

        if len(datasets_list) == 1:
            return datasets_list[0]

        union_str = f" UNION ALL SELECT * FROM ".join(datasets_list)
        return union_str

    def generate_filters(self, data_filter, extra_filters, main_paths, intersection_on):
        extra_filters = f"({extra_filters}) " if extra_filters else ""
        intersect_filter = self.generate_intersect_filter(main_paths, intersection_on)

        filters_str = " AND ".join(ftr for ftr in [data_filter, extra_filters, intersect_filter] if ftr)
        filters_str = f"WHERE {filters_str}" if filters_str else ""
        return filters_str

    @staticmethod
    def generate_intersect_filter(main_paths, intersection_on):
        if not intersection_on or len(main_paths) == 1:
            return ""

        intersect_select = " INTERSECT SELECT clip_name, grabindex FROM ".join(table for table in main_paths if table)
        intersect_select = f"(A.clip_name, A.grabindex) IN (SELECT clip_name, grabindex FROM {intersect_select})"
        return intersect_select

    @staticmethod
    def filter_paths(table_list: List[Table], dumps_to_include: List[str] = None):
        if not dumps_to_include:
            return [table.table_name for table in table_list]

        paths = [table.table_name for table in table_list if table.dataset_name in dumps_to_include]
        return paths


@dataclass
class CasesQuery(Query):
    """
    Defines the properties of cases graph

    Attributes:
            interesting_cases (dict): dict of cases names -> sql description of the case
    """

    interesting_cases: List[Case]
    sub_query: Query
    output_name: str = "cases"

    def get_query(self) -> str:
        cases = "\n".join(case.get_case_string() for case in self.interesting_cases)
        query = CASES_DESCRIPTION.format(
            cases=cases, output_name=self.output_name, sub_query=self.sub_query.get_query()
        )
        return query


@dataclass
class GroupByQuery(Query):
    """
    Defines the properties of group by graph

    Attributes:
            group_by_column (str): the column over which we count group by
    """

    group_by_columns: List[Column]
    sub_query: Query
    compute_percentage: bool = False
    metric: Metric = field(default_factory=CountMetric)

    def get_query(self) -> str:
        group_by = ",".join(col.name for col in self.group_by_columns)
        group_by = f", {group_by}" if group_by else ""
        query = COUNT_QUERY.format(
            sub_query=self.sub_query.get_query(),
            metric=self.metric.get_metric(),
            group_by=group_by,
            group_name="",
        )
        if self.compute_percentage:
            query = COUNT_PERCENTAGE.format(group_by=group_by, query=query)

        return query


@dataclass
class DiffQuery(Query):
    """
    Defines the properties of diff columns graph

    Attributes:
            group_by_column (str): the column over which we count group by
            diff_column (str): optional. column to compare to the group by column. computed as (abs(group_by - diff))
    """

    main_column: Column
    diff_column: Column
    sub_query: Query
    compute_percentage: bool = False
    output_name: str = "diff"
    metric: Metric = field(default_factory=CountMetric)

    def get_query(self) -> str:
        group_by = f", ABS({self.main_column.name} - {self.diff_column.name})"
        query = COUNT_QUERY.format(
            sub_query=self.sub_query.get_query(),
            metric=self.metric.get_metric(),
            group_by=group_by,
            group_name=f" AS {self.output_name}",
        )
        if self.compute_percentage:
            query = COUNT_PERCENTAGE.format(group_by=self.output_name, query=query)

        return query


@dataclass
class ConfMatQuery(Query):
    """
    Defines the properties of confusion matrix graph

    Attributes:
            column_to_compare (str): the relevant column to compare between 2 datasets
    """

    column_to_compare: Column
    main_data_query: Query
    secondary_data_query: Query

    def get_query(self) -> str:
        query = CONF_QUERY.format(
            main_data=self.main_data_query.get_query(),
            secondary_data=self.secondary_data_query.get_query(),
            column_to_compare=self.column_to_compare.name,
        )
        return query
