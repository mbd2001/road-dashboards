BASE_QUERY = """
    SELECT * FROM {meta_data} WHERE TRUE {meta_data_filters}
    """

COUNT_QUERY = """
    SELECT {group_by} AS {group_name}, {count_metric}
    FROM ({base_query})
    GROUP BY {group_by}
    """

DYNAMIC_QUERY = """
    SELECT {metrics}
    FROM ({base_query})
    """

COUNT_FILTER_METRIC = """
    COUNT(CASE WHEN {extra_filters} THEN 1 ELSE NULL END)
    AS overall_{ind}
    """

COUNT_ALL_METRIC = """
    COUNT(*) 
    AS {count_name}
    """


def generate_count_query(
    meta_data,
    group_by_column="",
    meta_data_filters="",
    extra_filters="",
    bins_factor=None,
):
    base_query = generate_base_query(
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
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
    meta_data,
    interesting_filters,
    meta_data_filters="",
    extra_filters="",
):
    metrics = ", ".join(
        COUNT_FILTER_METRIC.format(extra_filters=f"({filter})", ind=name)
        for name, filter in interesting_filters.items()
    )
    base_query = generate_base_query(
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
    )
    query = DYNAMIC_QUERY.format(metrics=metrics, base_query=base_query)
    return query


def generate_base_query(
    meta_data,
    meta_data_filters="",
    extra_filters="",
):
    meta_data_filters = "AND " + meta_data_filters if meta_data_filters else ""
    extra_filters = f"AND" + extra_filters if extra_filters else ""
    base_query = BASE_QUERY.format(
        meta_data=meta_data,
        meta_data_filters=meta_data_filters + extra_filters,
    )
    return base_query
