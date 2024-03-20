JOIN_QUERY = """
    SELECT main_val, secondary_val, COUNT(*) AS overall FROM
    (SELECT A.{column_to_compare} AS main_val, B.{column_to_compare} AS secondary_val
    FROM ({main_data}) A INNER JOIN ({secondary_data}) B
    ON ((A.clip_name = B.clip_name) AND (A.grabIndex = B.grabIndex)))
    GROUP BY main_val, secondary_val
    """

BASE_QUERY = """
    SELECT * FROM
    (SELECT * FROM
    ({base_data})
    {intersect_filter})
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
    main_table,
    secondary_table,
    population,
    column_to_compare,
    meta_data_filters="",
    extra_filters="",
    extra_columns=None,
):
    if isinstance(main_table, str):
        main_table = [main_table]

    if isinstance(secondary_table, str):
        secondary_table = [secondary_table]

    data_filters = generate_data_filters(meta_data_filters, extra_filters, population)
    main_data = generate_base_data(main_table, data_filters, extra_columns)
    secondary_data = generate_base_data(
        secondary_table, data_filters, extra_columns
    )  # TODO: consider remove filters from secondary_data
    query = JOIN_QUERY.format(
        main_data=main_data,
        secondary_data=secondary_data,
        column_to_compare=column_to_compare,
        data_filters=data_filters,
    )
    return query


def generate_count_query(
    md_tables,
    population,
    intersection_on,
    group_by_column="",
    meta_data_filters="",
    extra_filters="",
    bins_factor=None,
    extra_columns=None,
):
    base_query = generate_base_query(
        md_tables,
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
    md_tables,
    population,
    intersection_on,
    interesting_filters,
    meta_data_filters="",
    extra_filters="",
    extra_columns=None,
):
    metrics = ", ".join(
        COUNT_FILTER_METRIC.format(extra_filters=f"({filter})", ind=name)
        for name, filter in interesting_filters.items()
    )
    base_query = generate_base_query(
        md_tables,
        population,
        intersection_on,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=extra_columns,
    )
    query = DYNAMIC_QUERY.format(metrics=metrics, base_query=base_query)
    return query


def generate_base_query(
    md_tables,
    population,
    intersection_on,
    meta_data_filters="",
    extra_filters="",
    extra_columns=None,
):
    if isinstance(extra_columns, str):
        extra_columns = [extra_columns]

    if isinstance(md_tables, str):
        md_tables = [md_tables]

    data_filter = generate_data_filters(meta_data_filters, extra_filters, population)
    base_data = generate_base_data(md_tables, data_filter, extra_columns)
    intersect_filter = generate_intersect_filter(md_tables, intersection_on)
    base_query = BASE_QUERY.format(
        base_data=base_data,
        intersect_filter=intersect_filter,
    )
    return base_query


def generate_base_data(md_tables, data_filter, extra_columns=None):
    if extra_columns is None:
        extra_columns = []

    base_columns = ["dump_name", "clip_name", "grabIndex"]
    data_columns = ", ".join(base_columns + extra_columns)
    data_tables = [f"({md_table} {data_filter})" for md_table in md_tables if md_table]
    union_str = f" UNION ALL SELECT {data_columns} FROM ".join(data_tables)
    return f"SELECT {data_columns} FROM {union_str}"


def generate_intersect_filter(md_tables, intersection_on):
    if not intersection_on:
        return ""

    intersect_select = "SELECT clip_name, grabIndex FROM " + " INTERSECT SELECT clip_name, grabIndex FROM ".join(
        f"({md_table})" for md_table in md_tables if md_table
    )
    return f"WHERE (clip_name, grabIndex) IN ({intersect_select})"


def generate_data_filters(meta_data_filters, extra_filters, population):
    meta_data_filters = f"({meta_data_filters}) " if meta_data_filters else ""
    extra_filters = f"({extra_filters}) " if extra_filters else ""
    population_filter = f"(population = {population}) " if population != "all" else ""
    filters_str = " AND ".join(ftr for ftr in [meta_data_filters, extra_filters, population_filter] if ftr)
    filters_str = f"WHERE {filters_str}" if filters_str else ""
    return filters_str
