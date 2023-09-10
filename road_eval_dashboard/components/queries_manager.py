import numpy as np
import pandas as pd

from road_database_toolkit.athena.athena_utils import query_athena, athena_run_multiple_queries

BASE_QUERY = """
    SELECT * FROM
    (SELECT * FROM
    ({base_data})
    {intersect_filter}
    {stats_filters})
    INNER JOIN {meta_data} USING (clip_name, grabIndex)
    WHERE TRUE {meta_data_filters}
    """

JOIN_QUERY = """
    SELECT * FROM 
    ({t1})
    INNER JOIN
    ({t2})
    USING ({col})
    """

COUNT_QUERY = """
    SELECT {group_by} AS {group_name}, {count_metric}
    FROM ({base_query})
    GROUP BY {group_by}
    """

CONF_MAT_QUERY = """
    SELECT net_id, {label_col}, {pred_col}, COUNT(*) AS {count_name} 
    FROM ({base_query})
    GROUP BY net_id, {label_col}, {pred_col}
    """

DYNAMIC_METRICS_QUERY = """
    SELECT ({group_by}) AS net_id,
    {metrics}
    FROM ({base_query})
    GROUP BY ({group_by})
    """

GRAB_INDEX_HISTOGRAM_QUERY = """
    SELECT 
    {third_metrics_layer}
    FROM
    (SELECT clip_name,
    {second_metrics_layer}
    FROM
    (SELECT clip_name, grabIndex,
    {metrics}
    FROM ({base_query})
    GROUP BY clip_name, grabIndex)
    GROUP BY clip_name)
    """

COMPARE_QUERY = """
    SELECT net_id, CAST(COUNT(CASE WHEN ({label_col} {operator} {pred_col}) THEN 1 ELSE NULL END) AS DOUBLE) / COUNT(*) AS score 
    FROM ({base_query})
    GROUP BY net_id
    ORDER BY score
    """

COMPARE_METRIC = """
    CAST(COUNT(CASE WHEN ({label_col} {operator} {pred_col}) {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) /
    COUNT(CASE WHEN TRUE {extra_filters} THEN 1 ELSE NULL END)
    AS score_{ind}
    """

FB_PRECISION_METRIC = """
    CAST(COUNT(CASE WHEN match_score < 1 {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) /
    COUNT(CASE WHEN TRUE {extra_filters} THEN 1 ELSE NULL END) 
    AS precision_{ind}
    """

FB_CURVE_METRIC = """
    CAST(COUNT(CASE WHEN TRUE {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) / 
    COUNT(*)
    AS recall_{ind}
    """

FB_OVERALL_METRIC = """
    COUNT(CASE WHEN TRUE {extra_filters} THEN 1 ELSE NULL END)
    AS overall_{ind}
    """

MD_FILTER_COUNT = """
    COUNT(CASE WHEN TRUE {extra_filters} THEN 1 ELSE NULL END)
    AS count_{ind}
    """

DIST_METRIC = """
    CAST(COUNT(CASE WHEN "dist_{dist}" {thresh_filter} THEN 1 ELSE NULL END) AS DOUBLE) / 
    COUNT(CASE WHEN "dist_{dist}" IS NOT NULL THEN 1 ELSE NULL END)
    AS "score_{dist}"
    """

TP_METRIC = """
    CAST(COUNT(CASE WHEN {label_col} > 0 AND {pred_col} > {thresh} {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE)
    AS tp_{ind}
    """

TN_METRIC = """
    CAST(COUNT(CASE WHEN {label_col} < 0 AND {pred_col} <= {thresh} {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE)
    AS tn_{ind}
    """

PRECISION_METRIC = """
    CAST(COUNT(CASE WHEN {label_col} > 0 AND {pred_col} > {thresh} {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) /
    COUNT(CASE WHEN {pred_col} > {thresh} {extra_filters} THEN 1 ELSE NULL END)
    AS precision_{ind}
    """

RECALL_METRIC = """
    CAST(COUNT(CASE WHEN {label_col} > 0 AND {pred_col} > {thresh} {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) /
    COUNT(CASE WHEN {label_col} > 0 {extra_filters} THEN 1 ELSE NULL END)
    AS recall_{ind}
    """

COUNT_FILTER_METRIC = """
    COUNT(CASE WHEN {extra_filters} THEN 1 ELSE NULL END)
    AS overall_{ind}
    """

LOG_COUNT_METRIC = """
    LOG(2, COUNT(CASE WHEN {extra_filters} THEN 1 ELSE NULL END) + 1)
    AS overall_{ind}
    """

COUNT_ALL_METRIC = """
    COUNT(*) 
    AS {count_name}
    """

SUM_METRIC = """
    SUM({col})
    AS sum_{ind}
    """

CORRELATION_SUM_METRIC = """
    SUM({col}) - (POWER(SUM({col}) - 1, 2)) / (SUM({col}) + ((MAX(CASE WHEN {col} > 0 THEN grabIndex ELSE NULL END) - MIN(CASE WHEN {col} > 0 THEN grabIndex ELSE NULL END)) / 20))
    AS sum_{ind}
    """

THRESHOLDS = np.concatenate(
    (np.array([-1000]), np.linspace(-10, -1, 10), np.linspace(-1, 2, 31), np.linspace(2, 10, 9), np.array([1000]))
)

sec_to_dist_acc = {
    0.5: 0.2,
    1.0: 0.2,
    1.5: 0.23529411764705876,
    2.0: 0.3235294117647058,
    2.5: 0.4117647058823528,
    3.0: 0.49999999999999983,
    3.5: 0.5,
    4.0: 0.5,
    4.5: 0.5,
    5.0: 0.5,
}

sec_to_dist_falses = {
    0.5: 0.5,
    1.0: 0.5,
    1.5: 0.5270270270270272,
    2.0: 0.5945945945945947,
    2.5: 0.6621621621621623,
    3.0: 0.7,
    3.5: 0.7,
    4.0: 0.7,
    4.5: 0.7,
    5.0: 0.7,
}

distances = list(sec_to_dist_acc.keys())


def generate_grab_index_hist_query(
    data_tables,
    meta_data,
    interesting_filters,
):
    base_query = generate_base_query(data_tables, meta_data, only_meta_data=True)
    metrics = ", ".join(
        [LOG_COUNT_METRIC.format(extra_filters=f"({filter})", ind=name) for name, filter in interesting_filters.items()]
    )
    second_metrics_layer = ", ".join(
        [CORRELATION_SUM_METRIC.format(col=f"overall_{name}", ind=name) for name, filter in interesting_filters.items()]
    )
    third_metrics_layer = ", ".join(
        [SUM_METRIC.format(col=f"sum_{name}", ind=name) for name, filter in interesting_filters.items()]
    )
    query = GRAB_INDEX_HISTOGRAM_QUERY.format(
        metrics=metrics,
        second_metrics_layer=second_metrics_layer,
        third_metrics_layer=third_metrics_layer,
        base_query=base_query,
    )
    return query


def generate_vmax_success_rate_query(
    data_tables,
    meta_data,
    label_col,
    pred_col,
    interesting_filters,
    meta_data_filters="",
    extra_filters="",
):
    metrics = ", ".join(
        [
            TP_METRIC.format(
                thresh=0, label_col=label_col, pred_col=pred_col, extra_filters=f"AND ({filter})", ind=name
            )
            for name, filter in interesting_filters.items()
        ]
        + [
            TN_METRIC.format(
                thresh=0, label_col=label_col, pred_col=pred_col, extra_filters=f"AND ({filter})", ind=name
            )
            for name, filter in interesting_filters.items()
        ]
        + [
            COUNT_FILTER_METRIC.format(extra_filters=f"({filter})", ind=name)
            for name, filter in interesting_filters.items()
        ],
    )
    base_query = generate_base_query(
        data_tables,
        meta_data,
        extra_columns=[label_col, pred_col],
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        only_meta_data=True,
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    return query


def generate_vmax_fb_query(
    data_tables,
    meta_data,
    label_col,
    pred_col,
    interesting_filters,
    meta_data_filters="",
    extra_filters="",
):
    metrics = ", ".join(
        [
            RECALL_METRIC.format(
                thresh=0, label_col=label_col, pred_col=pred_col, extra_filters=f"AND ({filter})", ind=name
            )
            for name, filter in interesting_filters.items()
        ]
        + [
            PRECISION_METRIC.format(
                thresh=0, label_col=label_col, pred_col=pred_col, extra_filters=f"AND ({filter})", ind=name
            )
            for name, filter in interesting_filters.items()
        ]
    )
    base_query = generate_base_query(
        data_tables,
        meta_data,
        extra_columns=[label_col, pred_col],
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        only_meta_data=True,
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    return query


def generate_emdp_query(
    data_tables,
    meta_data,
    label_col,
    pred_col,
    interesting_filters,
    meta_data_filters="",
    extra_filters="",
    compare_operator="=",
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        extra_columns=[col for col in [label_col, pred_col] if isinstance(col, str)],
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        host=False,
        ca_oriented=False,
        only_meta_data=True,
    )
    metrics = ", ".join(
        COMPARE_METRIC.format(
            label_col=label_col, operator=compare_operator, pred_col=pred_col, extra_filters=f"AND ({filter})", ind=name
        )
        for name, filter in interesting_filters.items()
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    return query


def generate_path_net_query(
    data_tables,
    meta_data,
    state,
    meta_data_filters="",
    extra_filters="",
    host=False,
):
    operator = "<" if state == "acc" else ">"
    distances_dict = sec_to_dist_acc if state == "acc" else sec_to_dist_falses
    metrics = ", ".join(
        DIST_METRIC.format(thresh_filter=f"{operator} {thresh}", dist=sec, extra_filters="")
        for sec, thresh in distances_dict.items()
    )
    base_query = generate_base_query(
        data_tables,
        meta_data,
        extra_columns=[f'"dist_{sec}"' for sec, thresh in distances_dict.items()] + ["split_role"],
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        pathnet_oriented=True,
        host=host,
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    return query


def generate_fb_query(
    gt_data_tables,
    pred_data_tables,
    meta_data,
    interesting_filters={},
    input_thresh={},
    meta_data_filters="",
    extra_filters="",
    host=False,
):
    recall_query = generate_recall_query(
        gt_data_tables,
        meta_data,
        interesting_filters=interesting_filters,
        input_thresh=input_thresh,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        host=host,
    )

    precision_filter = "match_score >= 0"
    precision_query = generate_precision_query(
        pred_data_tables,
        meta_data,
        interesting_filters=interesting_filters,
        input_thresh=input_thresh,
        extra_columns=["match_score"],
        meta_data_filters=meta_data_filters,
        extra_filters=precision_filter if not extra_filters else f"{extra_filters} AND {precision_filter}",
        host=host,
    )

    final_query = JOIN_QUERY.format(t1=recall_query, t2=precision_query, col="net_id")
    return final_query


def generate_precision_query(
    data_tables,
    meta_data,
    interesting_filters={},
    input_thresh={},
    extra_columns=[],
    meta_data_filters="",
    extra_filters="",
    host=False,
):
    metrics = (
        get_fb_per_filter_metrics(interesting_filters, FB_PRECISION_METRIC)
        if interesting_filters
        else get_fb_curve_metrics(FB_PRECISION_METRIC)
    )
    base_query = generate_base_query(
        data_tables,
        meta_data,
        extra_columns=extra_columns,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        host=host,
    )
    group_by = get_fb_group_by(input_thresh)
    final_query = DYNAMIC_METRICS_QUERY.format(
        metrics=metrics, base_query=base_query, group_by=group_by if interesting_filters else "net_id"
    )
    return final_query


def generate_recall_query(
    data_tables,
    meta_data,
    interesting_filters={},
    input_thresh={},
    extra_columns=[],
    meta_data_filters="",
    extra_filters="",
    host=False,
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        extra_columns=extra_columns,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        host=host,
    )
    metrics = (
        get_fb_per_filter_metrics(interesting_filters, FB_OVERALL_METRIC)
        if interesting_filters
        else get_fb_curve_metrics(FB_CURVE_METRIC)
    )
    recall_query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    if not interesting_filters:
        return recall_query

    metrics = get_fb_per_filter_metrics(interesting_filters, MD_FILTER_COUNT)
    group_by = get_fb_group_by(input_thresh)
    md_count_query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by=group_by)

    final_query = JOIN_QUERY.format(t1=md_count_query, t2=recall_query, col="net_id")
    return final_query


def get_fb_per_filter_metrics(interesting_filters, metric):
    metrics = ", ".join(
        metric.format(extra_filters=f"AND ({filter})", ind=name) for name, filter in interesting_filters.items()
    )
    return metrics


def get_fb_curve_metrics(metric):
    metrics = ", ".join(
        metric.format(extra_filters=f"AND confidence >= {thresh}", ind=ind) for ind, thresh in enumerate(THRESHOLDS)
    )
    return metrics


def get_fb_group_by(input_thresh={}):
    if not input_thresh:
        group_by = "net_id"
        return group_by

    cases = "\n".join(
        f"WHEN net_id = '{net_id}' AND confidence >= {thresh} THEN '{net_id}'"
        for net_id, thresh in input_thresh.items()
    )
    group_by = f"CASE {cases} END"
    return group_by


def generate_conf_mat_query(
    data_tables,
    meta_data,
    label_col,
    pred_col,
    meta_data_filters="",
    extra_filters="",
    host=False,
    pathnet_oriented=False,
    ca_oriented=False,
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        extra_columns=[label_col, pred_col],
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        host=host,
        ca_oriented=ca_oriented,
        pathnet_oriented=pathnet_oriented,
    )
    conf_query = CONF_MAT_QUERY.format(
        label_col=label_col, pred_col=pred_col, base_query=base_query, count_name="res_count"
    )
    return conf_query


def generate_count_query(
    data_tables,
    meta_data,
    group_by_column="net_id",
    meta_data_filters="",
    extra_filters="",
    bins_factor=None,
    host=False,
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        host=host,
        only_meta_data=True,
    )
    metrics = COUNT_ALL_METRIC.format(count_name="overall")
    group_by = f"FLOOR({group_by_column} / {bins_factor}) * {bins_factor}" if bins_factor else group_by_column
    query = COUNT_QUERY.format(
        base_query=base_query, count_metric=metrics, group_by=group_by, group_name=group_by_column
    )
    return query


def generate_dynamic_count_query(
    data_tables,
    meta_data,
    interesting_filters,
    meta_data_filters="",
    extra_filters="",
    host=False,
):
    metrics = ", ".join(
        COUNT_FILTER_METRIC.format(extra_filters=f"({filter})", ind=name)
        for name, filter in interesting_filters.items()
    )
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        host=host,
        only_meta_data=True,
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    return query


def generate_compare_query(
    data_tables,
    meta_data,
    label_col,
    pred_col,
    meta_data_filters="",
    extra_filters="",
    host=False,
    compare_operator="=",
    ca_oriented=False,
    only_meta_data=False,
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        extra_columns=[col for col in [label_col, pred_col] if isinstance(col, str)],
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        host=host,
        ca_oriented=ca_oriented,
        only_meta_data=only_meta_data,
    )
    compare_query = COMPARE_QUERY.format(
        label_col=label_col, pred_col=pred_col, base_query=base_query, operator=compare_operator
    )
    return compare_query


def generate_base_query(
    data_tables,
    meta_data,
    extra_columns=[],
    meta_data_filters="",
    extra_filters="",
    host=False,
    ca_oriented=False,
    pathnet_oriented=False,
    only_meta_data=False,
):
    # TODO: remove generate_base_data if no big impact on performance
    base_data = generate_base_data(
        data_tables,
        extra_columns=extra_columns,
        ca_oriented=ca_oriented,
        pathnet_oriented=pathnet_oriented,
        only_meta_data=only_meta_data,
    )
    intersect_filter = generate_intersect_filter(data_tables)
    stats_filters = generate_stats_filters(ca_oriented, pathnet_oriented, extra_filters, host, only_meta_data)
    meta_data_filters = "AND " + meta_data_filters if meta_data_filters else ""
    base_query = BASE_QUERY.format(
        base_data=base_data,
        meta_data=meta_data,
        meta_data_filters=meta_data_filters,
        intersect_filter=intersect_filter,
        stats_filters=stats_filters,
    )
    return base_query


def generate_base_data(data_paths, extra_columns=[], ca_oriented=False, pathnet_oriented=False, only_meta_data=False):
    columns = ["clip_name", "grabIndex", "net_id"] + extra_columns
    if pathnet_oriented:
        columns += ["role"]
    elif ca_oriented:
        columns += ["ca_role", "match", "confidence"]
    elif not only_meta_data:
        columns += ["role", "ignore", "confidence"]

    column_str = ", ".join(columns)
    union_str = f" UNION ALL SELECT {column_str} FROM ".join(data_paths)
    return f"SELECT {column_str} FROM {union_str}"


def generate_stats_filters(
    ca_oriented=False,
    pathnet_oriented=False,
    extra_filters="",
    host=False,
    only_meta_data=False,
):
    ignore_string = (
        "confidence > 0 AND match <> -1 AND ca_role <> 'other'"
        if ca_oriented
        else ("" if only_meta_data or pathnet_oriented else f"ignore = FALSE")
    )
    role_string = (
        f"{'ca_role' if ca_oriented else 'role'} = 'host'"
        if host
        else ("" if not pathnet_oriented else "role = 'non-host'")
    )
    filters = [ignore_string, role_string, extra_filters]
    stats_filter = " AND ".join(ftr for ftr in filters if ftr)
    return f"AND {stats_filter}" if stats_filter else ""


def generate_intersect_filter(data_paths):
    intersect_select = "SELECT clip_name, grabIndex FROM " + " INTERSECT SELECT clip_name, grabIndex FROM ".join(
        data_paths
    )
    return f"WHERE (clip_name, grabIndex) IN ({intersect_select})"


def run_multiple_queries_with_nets_names_processing(query_list, database="run_eval_db"):
    dfs, s3_paths = athena_run_multiple_queries(database=database, query_list=query_list)
    dfs = [process_df_net_names(df) for df in dfs]
    return dfs, s3_paths


def run_query_with_nets_names_processing(query, database="run_eval_db"):
    df, s3_path = query_athena(database=database, query=query)
    df = process_df_net_names(df)
    return df, s3_path


def process_df_net_names(df, nets_names_col="net_id"):
    if nets_names_col in df.columns:
        df[nets_names_col] = df[nets_names_col].apply(process_net_name)
        df = df.sort_values(nets_names_col, ascending=False)
    return df


def process_net_name(net_name):
    if pd.isnull(net_name):
        return net_name
    return net_name.lstrip("0123456789-")
