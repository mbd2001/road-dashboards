from typing import List

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import BASE_COLUMNS, BaseColumn
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import Table

BASE_COLUMNS = [BaseColumn(col) for col in BASE_COLUMNS]

DIFF_COL = "difference"

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

CONF_QUERY = """
    SELECT main_val, secondary_val, COUNT(*) AS overall FROM (
        SELECT A.{column_to_compare} AS main_val, B.{column_to_compare} AS secondary_val
        FROM ({main_data}) A INNER JOIN ({secondary_data}) B
        ON ((A.clip_name = B.clip_name) AND (A.grabindex = B.grabindex) AND (A.obj_id = B.obj_id))
    )
    GROUP BY main_val, secondary_val
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

COUNT_QUERY = """
    SELECT dump_name, {group_by} {group_name}, {count_metric}
    FROM (
        {base_query}
    )
    GROUP BY dump_name, {group_by} ORDER BY dump_name
    """

DYNAMIC_QUERY = """
    SELECT dump_name, {metrics}
    FROM (
        {base_query}
    )
    GROUP BY dump_name ORDER BY dump_name
    """

CASES_DESCRIPTION = """
    SELECT *,
    CASE
        {cases}
        ELSE 'other'
    END AS cases
    FROM (
        {base_query}
    )
    """

COUNT_ALL_METRIC = """
    COUNT(*) 
    AS {count_name}
    """

COUNT_ALL_PRETTY_METRIC = """
    format_number(COUNT(*)) 
    AS {count_name}
    """

COUNT_PERCENTAGE = """
    WITH t1 AS (
        {query}
    )
    SELECT dump_name, {group_name}, (100.0 * overall) / (SUM(overall) OVER (PARTITION BY dump_name)) as percentage
    FROM t1
    """

IMG_LIMIT = 25


def generate_conf_mat_query(
    main_dump: str,
    secondary_dump: str,
    main_tables: Table,
    population: str,
    column_to_compare: BaseColumn,
    extra_columns: List[BaseColumn],
    meta_data_tables: Table = None,
    meta_data_filters: str = "",
    extra_filters: str = "",
):
    main_data = generate_base_query(
        main_tables,
        population,
        False,
        extra_columns,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        dumps_to_include=main_dump,
    )

    secondary_data = generate_base_query(
        main_tables,
        population,
        False,
        extra_columns,
        meta_data_tables=meta_data_tables,
        extra_filters=extra_filters,
        dumps_to_include=secondary_dump,
    )

    query = CONF_QUERY.format(
        main_data=main_data,
        secondary_data=secondary_data,
        column_to_compare=column_to_compare.name,
    )
    return query


def generate_diff_ids_query(
    main_dump: str,
    secondary_dump: str,
    main_tables: Table,
    population: str,
    column_to_compare: BaseColumn,
    meta_data_tables: Table = None,
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
    main_tables: Table,
    population: str,
    column_to_compare: BaseColumn,
    extra_columns: List[BaseColumn],
    meta_data_tables: Table = None,
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
        main_data=filter_paths(main_tables.tables_dict, [main_dump])[0],
        secondary_data=filter_paths(main_tables.tables_dict, [secondary_dump])[0],
    )
    return query


def generate_count_query(
    main_tables: Table,
    population: str,
    intersection_on: bool,
    extra_columns: List[BaseColumn],
    meta_data_tables: Table = None,
    main_column: BaseColumn = None,
    diff_column: BaseColumn = None,
    interesting_cases: dict = None,
    meta_data_filters: str = "",
    extra_filters: str = "",
    bins_factor: float = None,
    dumps_to_include: list[str] = None,
    compute_percentage: bool = False,
):
    base_query = generate_base_query(
        main_tables,
        population,
        intersection_on,
        extra_columns,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        dumps_to_include=dumps_to_include,
    )
    if not main_column and not interesting_cases:
        metrics = COUNT_ALL_PRETTY_METRIC.format(count_name="overall")
        query = DYNAMIC_QUERY.format(metrics=metrics, base_query=base_query)
        return query

    metrics = COUNT_ALL_METRIC.format(count_name="overall")
    if interesting_cases:
        cases = "\n".join(f"WHEN ({filter}) THEN '{name}'" for name, filter in interesting_cases.items())
        base_query = CASES_DESCRIPTION.format(cases=cases, base_query=base_query)
        group_by = group_name = "cases"
    else:
        col_metric = f"ABS({main_column.name} - {diff_column.name})" if diff_column else main_column.name
        group_by = f"FLOOR({col_metric} / {bins_factor}) * {bins_factor}" if bins_factor else col_metric
        group_name = DIFF_COL if diff_column else main_column.name

    query = COUNT_QUERY.format(
        base_query=base_query, count_metric=metrics, group_by=group_by, group_name=f" AS {group_name}"
    )
    if compute_percentage is True:
        query = COUNT_PERCENTAGE.format(group_name=group_name, query=query)
    return query


def generate_count_obj_query(
    main_tables: Table,
    population: str,
    intersection_on: bool,
    meta_data_tables: Table = None,
    meta_data_filters: str = "",
    extra_filters: str = "",
    dumps_to_include: str | List[str] = None,
    compute_percentage: bool = False,
):
    base_query = generate_base_query(
        main_tables,
        population,
        intersection_on,
        [],
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        dumps_to_include=dumps_to_include,
    )
    metrics = COUNT_ALL_METRIC.format(count_name="objects_per_frame")
    group_by = "clip_name, grabindex"
    query = COUNT_QUERY.format(base_query=base_query, count_metric=metrics, group_by=group_by, group_name="")
    metrics = COUNT_ALL_METRIC.format(count_name="overall")
    group_by = "objects_per_frame"
    query = COUNT_QUERY.format(base_query=query, count_metric=metrics, group_by=group_by, group_name="")
    if compute_percentage is True:
        query = COUNT_PERCENTAGE.format(group_name=group_by, query=query)
    return query


def generate_base_query(
    main_tables: Table,
    population: str,
    intersection_on: bool,
    extra_columns: List[BaseColumn],
    meta_data_tables: Table = None,
    meta_data_filters: str = None,
    extra_filters: str = None,
    dumps_to_include: str | List[str] = None,
):
    if isinstance(dumps_to_include, str):
        dumps_to_include = [dumps_to_include]

    main_paths = filter_paths(main_tables.tables_dict, dumps_to_include)
    meta_data_paths = filter_paths(meta_data_tables.tables_dict, dumps_to_include) if meta_data_tables else None
    filters = generate_filters(extra_filters, meta_data_filters, population, main_paths, intersection_on)
    base_data = generate_base_data(main_paths, filters, extra_columns, meta_data_paths)
    return base_data


def filter_paths(table_dict: dict, dumps_to_include: List[str] = None):
    if not dumps_to_include:
        return table_dict.values()

    paths = [path for dump, path in table_dict.items() if dump in dumps_to_include]
    return paths


def generate_base_data(
    main_paths: List[str], filters: str, extra_columns: List[BaseColumn], meta_data_paths: List[str] = None
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


def generate_intersect_filter(main_paths, intersection_on):
    if not intersection_on:
        return ""

    intersect_select = " INTERSECT SELECT clip_name, grabindex FROM ".join(table for table in main_paths if table)
    intersect_select = f"(A.clip_name, A.grabindex) IN (SELECT clip_name, grabindex FROM {intersect_select})"
    return intersect_select


def generate_filters(extra_filters, meta_data_filters, population, main_paths, intersection_on):
    extra_filters = f"({extra_filters}) " if extra_filters else ""
    meta_data_filters = f"({meta_data_filters}) " if meta_data_filters else ""
    population_filter = f"(A.population = '{population}') " if population != "all" else ""
    intersect_filter = generate_intersect_filter(main_paths, intersection_on)

    filters_str = " AND ".join(
        ftr for ftr in [extra_filters, meta_data_filters, population_filter, intersect_filter] if ftr
    )
    filters_str = f"WHERE {filters_str}" if filters_str else ""
    return filters_str
