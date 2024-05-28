from natsort import natsorted
from road_database_toolkit.athena.athena_utils import create_athena_table_from_query

from road_eval_dashboard.road_dump_dashboard.components.logical_components import (
    get_tables_property_union,
    get_value_from_tables_property_union,
)

COMMON_COLUMNS = {
    "population",
    "batch_num",
    "dump_name",
    "clip_name",
    "grabindex",
    "pred_name",
    "dump_name",
    "obj_id",
    "batch_num",
}

BASE_COLUMNS = ["population", "dump_name", "clip_name", "grabindex", "obj_id"]

DIFF_COL = "difference"

SELECT_QUERY = """
    (SELECT {columns_to_select} 
    FROM {main_data} A
    {filters})
    """

JOIN_QUERY = """
    (SELECT {columns_to_select} 
    FROM {main_data} A INNER JOIN {secondary_data} B
    ON ((A.clip_name = B.clip_name) AND (A.grabindex = B.grabindex)) 
    {filters})
    """

WITH_QUERY = """
    WITH {base_name} AS 
    ({query})
    {to_select}
    """

CONF_QUERY = """
    SELECT main_val, secondary_val, COUNT(*) AS overall FROM
    (SELECT A.{column_to_compare} AS main_val, B.{column_to_compare} AS secondary_val
    FROM ({main_data}) A INNER JOIN ({secondary_data}) B
    ON ((A.clip_name = B.clip_name) AND (A.grabindex = B.grabindex) AND (A.obj_id = B.obj_id)))
    GROUP BY main_val, secondary_val
    """

DIFF_IDS_QUERY = """
    SELECT A.clip_name as clip_name, A.grabindex as grabindex
    FROM ({main_data}) A INNER JOIN ({secondary_data}) B
    ON ((A.clip_name = B.clip_name) AND (A.grabindex = B.grabindex) AND (A.obj_id = B.obj_id))
    WHERE A.{column_to_compare} != B.{column_to_compare}
    GROUP BY A.clip_name, A.grabindex
    LIMIT {limit}
    """

JOIN_LABELS_QUERY = """
    SELECT '' AS main_start, {main_columns}, '' AS secondary_start, {secondary_columns}
    FROM ({main_labels}) LABELS_A FULL JOIN ({secondary_labels}) LABELS_B 
    ON ((LABELS_A.clip_name = LABELS_B.clip_name) AND (LABELS_A.grabindex = LABELS_B.grabindex) AND (LABELS_A.obj_id = LABELS_B.obj_id)) 
    WHERE (LABELS_A.clip_name, LABELS_A.grabindex) IN ({ids_data})
    """

COUNT_QUERY = """
    SELECT dump_name, {group_by} {group_name}, {count_metric}
    FROM ({base_query})
    GROUP BY dump_name, {group_by} ORDER BY dump_name
    """

DYNAMIC_QUERY = """
    SELECT dump_name, {metrics}
    FROM ({base_query})
    GROUP BY dump_name ORDER BY dump_name
    """

COUNT_FILTER_METRIC = """
    COUNT(CASE WHEN {extra_filters} THEN 1 ELSE NULL END) {divide_by_all}
    AS {ind}
    """

COUNT_ALL_METRIC = """
    COUNT(*) 
    AS {count_name}
    """

COUNT_PERCENTAGE = """
    WITH t1 AS ({query})
    SELECT dump_name, {group_name}, (100.0 * overall) / (SUM(overall) OVER (PARTITION BY dump_name)) as percentage
    FROM t1
    """

IMG_LIMIT = 25


def generate_conf_mat_query(
    main_dump,
    secondary_dump,
    main_tables,
    population,
    column_to_compare,
    meta_data_tables=None,
    meta_data_filters=None,
    extra_filters=None,
):
    main_data = generate_base_query(
        main_tables,
        population,
        False,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=column_to_compare,
        dumps_to_include=main_dump,
    )

    secondary_data = generate_base_query(
        main_tables,
        population,
        False,
        meta_data_tables=meta_data_tables,
        extra_filters=extra_filters,
        extra_columns=column_to_compare,
        dumps_to_include=secondary_dump,
    )

    query = CONF_QUERY.format(
        main_data=main_data,
        secondary_data=secondary_data,
        column_to_compare=column_to_compare,
    )
    return query


def generate_diff_query(
    main_dump,
    secondary_dump,
    main_tables,
    population,
    column_to_compare,
    meta_data_tables=None,
    meta_data_filters=None,
    extra_filters=None,
    limit=IMG_LIMIT,
):
    main_data = generate_base_query(
        main_tables,
        population,
        False,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=column_to_compare,
        dumps_to_include=main_dump,
    )

    secondary_data = generate_base_query(
        main_tables,
        population,
        False,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=column_to_compare,
        dumps_to_include=secondary_dump,
    )

    query = DIFF_IDS_QUERY.format(
        main_data=main_data,
        secondary_data=secondary_data,
        column_to_compare=column_to_compare,
        limit=limit,
    )
    return query


def generate_diff_with_labels_query(
    main_dump,
    secondary_dump,
    main_tables,
    labels_tables,
    population,
    column_to_compare,
    meta_data_tables=None,
    meta_data_filters=None,
    extra_filters=None,
    limit=IMG_LIMIT,
):
    diff_query = generate_diff_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        column_to_compare,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        limit=limit,
    )
    query = JOIN_LABELS_QUERY.format(
        main_columns=", ".join(f"LABELS_A.{col}" for col in labels_tables["columns_to_type"].keys()),
        secondary_columns=", ".join(f"LABELS_B.{col}" for col in labels_tables["columns_to_type"].keys()),
        main_labels=labels_tables["tables_dict"][main_dump],
        secondary_labels=labels_tables["tables_dict"][secondary_dump],
        ids_data=diff_query,
    )
    return query


def generate_count_query(
    main_tables,
    population,
    intersection_on,
    meta_data_tables=None,
    main_column=None,
    diff_column=None,
    meta_data_filters=None,
    extra_filters=None,
    bins_factor=None,
    dumps_to_include=None,
    compute_percentage=False,
):
    base_query = generate_base_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=[col for col in [main_column, diff_column] if col is not None],
        dumps_to_include=dumps_to_include,
    )
    metrics = COUNT_ALL_METRIC.format(count_name="overall")
    if main_column is None:
        query = DYNAMIC_QUERY.format(metrics=metrics, base_query=base_query)
        return query

    col_metric = f"ABS({main_column} - {diff_column})" if diff_column else main_column
    group_by = (
        f"FLOOR({col_metric} / {bins_factor}) * {bins_factor}" if bins_factor and bins_factor != 1 else col_metric
    )
    group_name = DIFF_COL if diff_column else main_column
    query = COUNT_QUERY.format(
        base_query=base_query, count_metric=metrics, group_by=group_by, group_name=f" AS {group_name}"
    )
    if compute_percentage is True:
        query = COUNT_PERCENTAGE.format(group_name=group_name, query=query)
    return query


def generate_count_obj_query(
    main_tables,
    population,
    intersection_on,
    meta_data_tables=None,
    meta_data_filters=None,
    extra_filters=None,
    dumps_to_include=None,
    compute_percentage=False,
):
    base_query = generate_base_query(
        main_tables,
        population,
        intersection_on,
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


def generate_dynamic_count_query(
    main_tables,
    population,
    intersection_on,
    interesting_filters,
    meta_data_tables=None,
    meta_data_filters=None,
    extra_filters=None,
    compute_percentage=False,
):
    divide_by_all = "* 100.0 / COUNT(*)" if compute_percentage is True else ""
    metrics = ", ".join(
        COUNT_FILTER_METRIC.format(extra_filters=f"({filter})", ind=name, divide_by_all=divide_by_all)
        for name, filter in interesting_filters["filters"].items()
    )
    base_query = generate_base_query(
        main_tables,
        population,
        intersection_on,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=interesting_filters["extra_columns"],
    )
    query = DYNAMIC_QUERY.format(metrics=metrics, base_query=base_query)
    return query


def generate_base_query(
    main_tables,
    population,
    intersection_on,
    meta_data_tables=None,
    meta_data_filters=None,
    extra_filters=None,
    extra_columns=None,
    dumps_to_include=None,
):
    if isinstance(extra_columns, str):
        extra_columns = [extra_columns]

    if isinstance(dumps_to_include, str):
        dumps_to_include = [dumps_to_include]

    main_paths = filter_paths(main_tables["tables_dict"], dumps_to_include)
    meta_data_paths = filter_paths(meta_data_tables["tables_dict"], dumps_to_include) if meta_data_tables else None
    type_filters = filter_ignore_multiple_columns(extra_columns, main_tables, meta_data_tables)
    agg_cols, extra_columns = get_aggregated_columns(extra_columns, main_tables, meta_data_tables)
    filters = generate_filters(extra_filters, meta_data_filters, population, main_paths, intersection_on, type_filters)
    base_data = generate_base_data(main_paths, filters, meta_data_paths, extra_columns)
    if agg_cols:
        base_data = generate_agg_cols_union(agg_cols, base_data, main_tables, meta_data_tables)

    return base_data


def get_aggregated_columns(extra_columns, main_tables, meta_data_tables=None):
    if not extra_columns:
        return {}, extra_columns

    existing_cols = get_tables_property_union(main_tables, meta_data_tables, "columns_to_type")
    matching_columns = {
        agg_col: natsorted([col for col in existing_cols.keys() if col.startswith(agg_col)])
        for agg_col in extra_columns
    }
    matching_columns = {agg_col: matching for agg_col, matching in matching_columns.items() if len(matching) > 1}
    if not matching_columns:
        return {}, extra_columns

    for key, val in matching_columns.items():
        extra_columns.remove(key)
        extra_columns.extend(val)
    return matching_columns, extra_columns


def generate_agg_cols_union(agg_cols, base_query, main_tables, meta_data_tables=None):
    base_query = create_athena_table_from_query(base_query, database="run_eval_db")
    base_columns = ", ".join(BASE_COLUMNS)
    select_strings = [
        ", ".join(f"{col} AS {agg_col}" for col, agg_col in zip(col_list, agg_cols.keys()))
        for col_list in zip(*agg_cols.values())
    ]
    filter_strings = [
        (
            f"WHERE {filter_str}"
            if (filter_str := filter_ignore_multiple_columns(col_list, main_tables, meta_data_tables))
            else ""
        )
        for col_list in zip(*agg_cols.values())
    ]
    final_query = " UNION ALL ".join(
        f"SELECT {select_str}, {base_columns} FROM {base_query} {filter_str}"
        for select_str, filter_str in zip(select_strings, filter_strings)
    )
    return final_query


def filter_paths(table_dict, dumps_to_include):
    if not dumps_to_include:
        return table_dict.values()

    paths = [path for dump, path in table_dict.items() if dump in dumps_to_include]
    return paths


def generate_base_data(main_paths, filters, meta_data_paths=None, extra_columns=None):
    if extra_columns is None:
        extra_columns = []

    desired_columns = set(BASE_COLUMNS + extra_columns)
    if meta_data_paths:
        datasets_list = generate_joined_data(main_paths, meta_data_paths, desired_columns, filters)
    else:
        datasets_list = generate_single_data(main_paths, desired_columns, filters)

    if len(datasets_list) == 1:
        return datasets_list[0]

    union_str = f" UNION ALL SELECT * FROM ".join(datasets_list)
    return union_str


def generate_joined_data(main_paths, meta_data_paths, desired_columns, filters):
    data_columns_str = ", ".join(manipulate_column_to_avoid_ambiguities(col) for col in desired_columns)
    join_strings = [
        JOIN_QUERY.format(
            columns_to_select=data_columns_str,
            main_data=main_table,
            secondary_data=md_table,
            filters=filters,
        )
        for main_table, md_table in zip(main_paths, meta_data_paths)
        if main_table
    ]
    return join_strings


def manipulate_column_to_avoid_ambiguities(col, as_original_col=True):
    manipulated_column = f"A.{col}" if col in COMMON_COLUMNS else col
    manipulated_column = f"{manipulated_column} AS {col}" if as_original_col else manipulated_column
    return manipulated_column


def generate_single_data(main_paths, desired_columns, filters):
    data_columns_str = ", ".join(desired_columns)
    datasets_strings = [
        SELECT_QUERY.format(columns_to_select=data_columns_str, main_data=main_table, filters=filters)
        for main_table in main_paths
        if main_table
    ]
    return datasets_strings


def generate_intersect_filter(main_paths, intersection_on):
    if not intersection_on:
        return ""

    intersect_select = " INTERSECT SELECT clip_name, grabindex FROM ".join(table for table in main_paths if table)
    intersect_select = f"(A.clip_name, A.grabindex) IN (SELECT clip_name, grabindex FROM {intersect_select})"
    return intersect_select


def generate_filters(extra_filters, meta_data_filters, population, main_paths, intersection_on, type_filters):
    type_filters = f"({type_filters}) " if type_filters else ""
    extra_filters = f"({extra_filters}) " if extra_filters else ""
    meta_data_filters = f"({meta_data_filters}) " if meta_data_filters else ""
    population_filter = f"(A.population = '{population}') " if population != "all" else ""
    intersect_filter = generate_intersect_filter(main_paths, intersection_on)

    filters_str = " AND ".join(
        ftr for ftr in [type_filters, extra_filters, meta_data_filters, population_filter, intersect_filter] if ftr
    )
    filters_str = f"WHERE {filters_str}" if filters_str else ""
    return filters_str


def filter_ignore_multiple_columns(columns, main_tables, meta_data_tables):
    if not columns:
        return ""

    if isinstance(columns, str):
        columns = [columns]

    filters = [filter_ignore_single_column(column, main_tables, meta_data_tables) for column in columns]
    filters_str = " AND ".join(f"({ftr})" for ftr in filters if ftr)
    return filters_str


def filter_ignore_single_column(column, main_tables, meta_data_tables):
    column_type = get_value_from_tables_property_union(column, main_tables, meta_data_tables)
    if column_type is None:
        return ""

    column = manipulate_column_to_avoid_ambiguities(column, as_original_col=False)
    if column_type.startswith(("int", "float", "double")):
        ignore_filter = f"{column} <> -1 AND {column} BETWEEN -998 AND 998"
    elif column_type.startswith("object"):
        ignore_filter = f"{column} NOT IN ('ignore', 'Unknown', 'IGNORE')"
    else:
        ignore_filter = ""
    return ignore_filter
