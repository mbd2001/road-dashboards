BASE_QUERY = """
    SELECT * FROM
    (SELECT * FROM
    ({base_data})
    {intersect_filter})
    WHERE TRUE {data_filters}
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


def generate_count_query(
    md_tables,
    intersection_on,
    group_by_column="",
    meta_data_filters="",
    extra_filters="",
    bins_factor=None,
    extra_columns=None,
):
    base_query = generate_base_query(
        md_tables,
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
        intersection_on,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=extra_columns,
    )
    query = DYNAMIC_QUERY.format(metrics=metrics, base_query=base_query)
    return query


def generate_base_query(
    md_tables,
    intersection_on,
    meta_data_filters="",
    extra_filters="",
    extra_columns=None,
):
    if extra_columns is None:
        extra_columns = []

    if not isinstance(extra_columns, list):
        extra_columns = [extra_columns]

    base_data = generate_base_data(md_tables, extra_columns)
    intersect_filter = generate_intersect_filter(md_tables, intersection_on)
    meta_data_filters = f" AND ({meta_data_filters})" if meta_data_filters else ""
    extra_filters = f" AND " + extra_filters if extra_filters else ""
    base_query = BASE_QUERY.format(
        base_data=base_data,
        intersect_filter=intersect_filter,
        data_filters=meta_data_filters + extra_filters,
    )
    return base_query


def generate_base_data(md_tables, extra_columns):
    base_columns = ["dump_name", "clip_name", "grabIndex"]
    data_columns = ", ".join(base_columns + extra_columns)
    union_str = f" UNION ALL SELECT {data_columns} FROM ".join(md_table for md_table in md_tables if md_table)
    return f"SELECT {data_columns} FROM {union_str}"


def generate_intersect_filter(md_tables, intersection_on):
    if not intersection_on:
        return ""

    intersect_select = "SELECT clip_name, grabIndex FROM " + " INTERSECT SELECT clip_name, grabIndex FROM ".join(
        md_table for md_table in md_tables if md_table
    )
    return f"WHERE (clip_name, grabIndex) IN ({intersect_select})"
