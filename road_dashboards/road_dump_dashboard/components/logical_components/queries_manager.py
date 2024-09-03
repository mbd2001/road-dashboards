from typing import List

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import Column
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import TableType

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


IMG_LIMIT = 25


def generate_diff_ids_query(
    main_dump: str,
    secondary_dump: str,
    main_tables: TableType,
    population: str,
    column_to_compare: Column,
    meta_data_tables: TableType = None,
    meta_data_filters: str = "",
    extra_filters: str = "",
    limit: int = IMG_LIMIT,
):
    main_data = generate_base_query(
        main_tables,
        population,
        False,
        [column_to_compare],
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        dumps_to_include=main_dump,
    )
    secondary_data = generate_base_query(
        main_tables,
        population,
        False,
        [column_to_compare],
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        dumps_to_include=secondary_dump,
    )

    query = DIFF_IDS_QUERY.format(
        main_data=main_data,
        secondary_data=secondary_data,
        column_to_compare=column_to_compare.name,
        limit=limit,
    )
    return query


def generate_diff_labels_query(
    main_dump: str,
    secondary_dump: str,
    main_tables: TableType,
    population: str,
    column_to_compare: Column,
    extra_columns: List[Column],
    meta_data_tables: TableType = None,
    meta_data_filters: str = "",
    extra_filters: str = "",
    limit: int = IMG_LIMIT,
):
    diff_ids_query = generate_diff_ids_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        column_to_compare,
        meta_data_tables,
        meta_data_filters,
        extra_filters,
        limit,
    )

    agg_columns = ", ".join(f"array_agg({col.name}) as {col.name}" for col in extra_columns)
    label_columns = ", ".join(col.name for col in extra_columns)
    query = DIFF_LABELS_QUERY.format(
        diff_ids_query=diff_ids_query,
        agg_columns=agg_columns,
        label_columns=label_columns,
        main_data=filter_paths(main_tables.tables, [main_dump])[0],
        secondary_data=filter_paths(main_tables.tables, [secondary_dump])[0],
    )
    return query
