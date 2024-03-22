COMMON_COLUMNS = {
    "population",
    "batch_num",
    "dump_name",
    "clip_name",
    "grabIndex",
    "grabindex",
    "pred_name",
    "dump_name",
}

BASE_COLUMNS = ["population", "dump_name", "clip_name", "grabIndex"]

SELECT_QUERY = """
    (SELECT {columns_to_select} 
    FROM {main_data} A
    {meta_data_filters})
    """

JOIN_QUERY = """
    (SELECT {columns_to_select} 
    FROM {main_data} A INNER JOIN {secondary_data} B
    ON ((A.clip_name = B.clip_name) AND (A.grabIndex = B.grabIndex)) 
    {meta_data_filters})
    """

CONF_QUERY = """
    SELECT main_val, secondary_val, COUNT(*) AS overall FROM
    (SELECT A.{column_to_compare} AS main_val, B.{column_to_compare} AS secondary_val
    FROM ({main_data}) A INNER JOIN ({secondary_data}) B
    ON ((A.clip_name = B.clip_name) AND (A.grabIndex = B.grabIndex)))
    GROUP BY main_val, secondary_val
    """

COUNT_QUERY = """
    SELECT dump_name, {group_by} AS {group_name}, {count_metric}
    FROM ({base_query})
    GROUP BY dump_name, {group_by}
    """

DYNAMIC_QUERY = """
    SELECT dump_name, {metrics}
    FROM ({base_query})
    GROUP BY dump_name
    """

COUNT_FILTER_METRIC = """
    COUNT(CASE WHEN {extra_filters} THEN 1 ELSE NULL END)
    AS {ind}
    """

COUNT_ALL_METRIC = """
    COUNT(*) 
    AS {count_name}
    """


def generate_conf_mat_query(
    main_dump,
    secondary_dump,
    main_tables,
    population,
    column_to_compare,
    meta_data_tables=None,
    meta_data_filters="",
    extra_filters="",
):
    extra_columns = [column_to_compare] if column_to_compare else None
    main_identifier = f" dump_name = '{main_dump}' "
    main_data = generate_base_query(
        main_tables,
        meta_data_tables,
        population,
        False,
        meta_data_filters=meta_data_filters,
        extra_filters=f" ({extra_filters}) AND ({main_identifier}) " if extra_filters else main_identifier,
        extra_columns=extra_columns,
    )

    secondary_identifier = f" dump_name = '{secondary_dump}' "
    secondary_data = generate_base_query(
        main_tables,
        meta_data_tables,
        population,
        False,
        extra_filters=f" ({extra_filters}) AND ({secondary_identifier}) " if extra_filters else secondary_identifier,
        extra_columns=extra_columns,
    )

    query = CONF_QUERY.format(
        main_data=main_data,
        secondary_data=secondary_data,
        column_to_compare=column_to_compare,
    )
    return query


def generate_count_query(
    main_tables,
    population,
    intersection_on,
    meta_data_tables=None,
    group_by_column="",
    meta_data_filters="",
    extra_filters="",
    bins_factor=None,
):
    base_query = generate_base_query(
        main_tables,
        meta_data_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=[group_by_column] if group_by_column else None,
    )
    if group_by_column:
        metrics = COUNT_ALL_METRIC.format(count_name="overall")
        group_by = f"FLOOR({group_by_column} / {bins_factor}) * {bins_factor}" if bins_factor else group_by_column
        query = COUNT_QUERY.format(
            base_query=base_query, count_metric=metrics, group_by=group_by, group_name=group_by_column
        )
    else:
        metrics = "COUNT(*) AS overall"
        query = DYNAMIC_QUERY.format(metrics=metrics, base_query=base_query)

    return query


def generate_dynamic_count_query(
    main_tables,
    population,
    intersection_on,
    interesting_filters,
    meta_data_tables=None,
    meta_data_filters="",
    extra_filters="",
    extra_columns=None,
):
    metrics = ", ".join(
        COUNT_FILTER_METRIC.format(extra_filters=f"({filter})", ind=name)
        for name, filter in interesting_filters["filters"].items()
    )
    base_query = generate_base_query(
        main_tables,
        meta_data_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=interesting_filters["extra_columns"],
    )
    query = DYNAMIC_QUERY.format(metrics=metrics, base_query=base_query)
    return query


def generate_base_query(
    main_tables,
    meta_data_tables,
    population,
    intersection_on,
    meta_data_filters="",
    extra_filters="",
    extra_columns=None,
):
    if isinstance(extra_columns, str):
        extra_columns = [extra_columns]

    main_paths = main_tables["tables_dict"].values()
    meta_data_paths = meta_data_tables["tables_dict"].values() if meta_data_tables else None

    intersect_filter = generate_intersect_filter(main_paths, intersection_on)
    filters = generate_extra_filters(extra_filters, intersect_filter, meta_data_filters, population)
    base_data = generate_base_data(main_paths, meta_data_paths, filters, extra_columns)
    return base_data


def generate_base_data(main_paths, meta_data_paths, filters, extra_columns=None):
    if extra_columns is None:
        extra_columns = []

    desired_columns = set(BASE_COLUMNS + extra_columns)
    if meta_data_paths:
        datasets_list = generate_joined_data(main_paths, meta_data_paths, desired_columns, filters)
    else:
        datasets_list = generate_single_data(main_paths, desired_columns, filters)

    union_str = f" UNION ALL SELECT * FROM ".join(datasets_list)
    union_str = f"SELECT * FROM {union_str}"
    return union_str


def generate_joined_data(main_paths, meta_data_paths, desired_columns, meta_data_filters):
    data_columns_str = ", ".join(manipulate_column_to_avoid_ambiguities(col) for col in desired_columns)
    join_strings = [
        JOIN_QUERY.format(
            columns_to_select=data_columns_str,
            main_data=main_table,
            secondary_data=md_table,
            meta_data_filters=meta_data_filters,
        )
        for main_table, md_table in zip(main_paths, meta_data_paths)
        if main_table
    ]
    return join_strings


def manipulate_column_to_avoid_ambiguities(col):
    manipulated_column = f"A.{col} AS {col}" if col in COMMON_COLUMNS else col
    return manipulated_column


def generate_single_data(main_paths, desired_columns, meta_data_filters):
    data_columns_str = ", ".join(desired_columns)
    datasets_strings = [
        SELECT_QUERY.format(
            columns_to_select=data_columns_str, main_data=main_table, meta_data_filters=meta_data_filters
        )
        for main_table in main_paths
        if main_table
    ]
    return datasets_strings


def generate_intersect_filter(main_paths, intersection_on):
    if not intersection_on:
        return ""

    intersect_select = " INTERSECT SELECT clip_name, grabIndex FROM ".join(table for table in main_paths if table)
    intersect_select = f"(A.clip_name, A.grabIndex) IN (SELECT clip_name, grabIndex FROM {intersect_select})"
    return intersect_select


def generate_extra_filters(extra_filters, intersect_filter, meta_data_filters, population):
    extra_filters = f"({extra_filters}) " if extra_filters else ""
    meta_data_filters = f"({meta_data_filters}) " if meta_data_filters else ""
    population_filter = f"(A.population = '{population}') " if population != "all" else ""

    filters_str = " AND ".join(
        ftr for ftr in [extra_filters, intersect_filter, meta_data_filters, population_filter] if ftr
    )
    filters_str = f"WHERE {filters_str}" if filters_str else ""
    return filters_str
