from road_dashboards.road_eval_dashboard.components.queries_manager import (
    DYNAMIC_METRICS_QUERY,
    generate_base_data,
    generate_intersect_filter,
)


def get_falses_query(
    data_tables,
    meta_data,
    interesting_filters,
    Z_source,
    meta_data_filters="",
    extra_columns=[],
    role="",
):
    BASE_QUERY = """
        SELECT * FROM
        (SELECT clip_name, grabIndex, net_id, match, COUNT(*) as group_size, MIN(rem_{Z_source}_point_sec) as rem_point_sec, MIN(rem_{Z_source}_point_Z) as rem_point_z FROM (SELECT * FROM
        ({base_data})
        {intersect_filter})
        WHERE ignore=False AND confidence > 0 AND role='{role}' AND rem_{Z_source}_point_index >= 0
        group by net_id, clip_name, grabIndex, match)
        INNER JOIN ({meta_data}) USING (clip_name, grabIndex)
        WHERE TRUE {meta_data_filters}
        """

    FALSE_GT_METRIC = """
    SUM(CASE WHEN match <> -1 {extra_filters} THEN group_size - 1 ELSE 0 END) as "score_gt_{ind}"
    """
    FALSE_NONE_GT_METRIC = """
        SUM(CASE WHEN match = -1 {extra_filters} THEN group_size ELSE 0 END) as "score_none_gt_{ind}"
        """
    COUNT_METRIC = """
    SUM(CASE WHEN TRUE {extra_filters} THEN group_size ELSE 0 END) as "count_{ind}"
"""
    metrics_list = []
    for metric in [COUNT_METRIC, FALSE_GT_METRIC, FALSE_NONE_GT_METRIC]:
        metrics_list += [
            metric.format(extra_filters=f"AND ({filter})", ind=name) for name, filter in interesting_filters.items()
        ]
    metrics = ", ".join(metrics_list)

    base_data = generate_base_data(data_tables["paths"], data_tables["required_columns"], extra_columns)
    intersect_filter = generate_intersect_filter(data_tables["paths"])
    base_query = BASE_QUERY.format(
        base_data=base_data,
        intersect_filter=intersect_filter,
        role=role,
        meta_data=meta_data,
        meta_data_filters=meta_data_filters,
        Z_source=Z_source,
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    return query
