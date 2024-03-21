SELECT_QUERY = """
    (SELECT {columns_to_select} 
    FROM {main_data} B
    {meta_data_filters})
    """

JOIN_QUERY = """
    (SELECT {columns_to_select} 
    FROM {main_data} A INNER JOIN {secondary_data} B
    ON ((A.clip_name = B.clip_name) AND (A.grabIndex = B.grabIndex)) 
    {meta_data_filters})
    """

BASE_QUERTY = """
    SELECT * FROM
    ({base_data})
    {extra_filters} 
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
    extra_columns=None,
):
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
        meta_data_filters=meta_data_filters,  # TODO: consider remove filters from secondary_data
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
    extra_columns=None,
):
    base_query = generate_base_query(
        main_tables,
        meta_data_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=extra_columns,
    )
    if not group_by_column:
        metrics = "COUNT(*) AS overall"
        query = DYNAMIC_QUERY.format(metrics=metrics, base_query=base_query)
    else:
        metrics = COUNT_ALL_METRIC.format(count_name="overall")
        group_by = f"FLOOR({group_by_column} / {bins_factor}) * {bins_factor}" if bins_factor else group_by_column
        query = COUNT_QUERY.format(
            base_query=base_query, count_metric=metrics, group_by=group_by, group_name=group_by_column
        )
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
        for name, filter in interesting_filters.items()
    )
    base_query = generate_base_query(
        main_tables,
        meta_data_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=extra_columns,
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

    main_columns = main_tables["columns_to_type"].keys()
    main_paths = main_tables["tables_dict"].values()
    meta_data_paths = meta_data_tables["tables_dict"].values() if meta_data_tables else None

    meta_data_filters = f"({meta_data_filters}) " if meta_data_filters else ""
    base_data = generate_base_data(main_paths, meta_data_paths, meta_data_filters, main_columns, extra_columns)

    intersect_filter = generate_intersect_filter(main_paths, intersection_on)
    extra_filters = generate_extra_filters(extra_filters, intersect_filter, population)

    base_data = BASE_QUERTY.format(base_data=base_data, extra_filters=extra_filters)
    return base_data


def generate_base_data(main_paths, meta_data_paths, meta_data_filters, main_columns, extra_columns=None):
    if extra_columns is None:
        extra_columns = []

    base_columns = ["population", "dump_name", "clip_name", "grabIndex"]
    data_columns = set(base_columns + extra_columns)
    if meta_data_paths:
        data_columns_str = ", ".join(
            f"A.{col} AS {col}" if is_column_in_primary_table(col, main_columns) else f"B.{col} AS {col}"
            for col in data_columns
        )
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
    else:
        data_columns_str = ", ".join(data_columns)
        join_strings = [
            SELECT_QUERY.format(
                columns_to_select=data_columns_str, main_data=main_table, meta_data_filters=meta_data_filters
            )
            for main_table in main_paths
            if main_table
        ]
    union_str = f" UNION ALL SELECT * FROM ".join(join_strings)
    return f"SELECT * FROM {union_str}"


def is_column_in_primary_table(col, columns_in_table):
    return col in columns_in_table or col.lower() in columns_in_table


def generate_intersect_filter(main_names, intersection_on):
    if not intersection_on:
        return ""

    intersect_select = " INTERSECT SELECT clip_name, grabIndex FROM ".join(
        md_table for md_table in main_names if md_table
    )
    intersect_select = f"(clip_name, grabIndex) IN (SELECT clip_name, grabIndex FROM {intersect_select})"
    return intersect_select


def generate_extra_filters(extra_filters, intersect_filter, population):
    extra_filters = f"({extra_filters}) " if extra_filters else ""

    population_filter = f"(population = '{population}') " if population != "all" else ""

    filters_str = " AND ".join(ftr for ftr in [extra_filters, intersect_filter, population_filter] if ftr)
    filters_str = f"WHERE {filters_str}" if filters_str else ""
    return filters_str
