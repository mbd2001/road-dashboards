import enum
import re

import numpy as np
import pandas as pd
from road_database_toolkit.athena.athena_utils import athena_run_multiple_queries, query_athena

PATHNET_IGNORE = 990
PATHNET_BASE_DIST = 0.5

BASE_QUERY = """
    SELECT * FROM
    (SELECT * FROM
    ({base_data})
    {intersect_filter}
    {stats_filters})
    INNER JOIN ({meta_data}) USING (clip_name, grabIndex)
    WHERE TRUE {meta_data_filters}
    """

COLS_QUERY = """
    SELECT TABLE_NAME, COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME IN ({paths}) AND COLUMN_NAME LIKE '%{search_string}%'
    ORDER BY TABLE_NAME, COLUMN_NAME
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
    SELECT net_id, {group_by_label} as {label_col}, {group_by_pred} as {pred_col}, COUNT(*) AS {count_name}
    FROM ({base_query})
    GROUP BY net_id, {group_by_label}, {group_by_pred}
    """

COLUMN_OPTION_QUERY = """
    SELECT DISTINCT {column_name}
    FROM ({base_query})
"""


DYNAMIC_METRICS_QUERY = """
    SELECT ({group_by}) AS net_id,
    {metrics}
    FROM ({base_query})
    GROUP BY ({group_by})
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
    AS "score_{ind}"
    """

SUM_BY_CASE_METRIC = """
    CAST(SUM(CASE WHEN ({extra_filters}) THEN {col_name} ELSE 0 END) AS DOUBLE)
    AS "score_{ind}"
    """

FB_PRECISION_METRIC = """
    CAST(COUNT(CASE WHEN match_score < 1 {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) /
    COUNT(CASE WHEN TRUE {extra_filters} THEN 1 ELSE NULL END)
    AS precision_{ind}
    """

PATHNET_THRESHOLD_METRIC = """
    CAST(COUNT(CASE WHEN "{column}" < {threshold} THEN 1 ELSE NULL END) AS DOUBLE) /
    COUNT(*)
    AS precision_{ind}
    """


ROC_STATS_METRIC = """
    CAST(COUNT(CASE WHEN {label_col} > 0 AND {pred_col} >= {threshold} {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) AS tp_{ind},
    CAST(COUNT(CASE WHEN {label_col} < 0 AND {pred_col} >= {threshold} {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) AS fp_{ind},
    CAST(COUNT(CASE WHEN {label_col} < 0 AND {pred_col} <  {threshold} {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) AS tn_{ind},
    CAST(COUNT(CASE WHEN {label_col} > 0 AND {pred_col} <  {threshold} {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) AS fn_{ind}
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
    AS "count_{ind}"
    """

DIST_METRIC = """
    CAST(COUNT(CASE WHEN "{base_dist_column_name}_{dist}" IS NOT NULL AND "{base_dist_column_name}_{dist}" {thresh_filter} {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) / 
    COUNT(CASE WHEN ("{base_dist_column_name}_{dist}" IS NOT NULL) {extra_filters} THEN 1 ELSE NULL END)
    AS "score_{ind}"
    """

DP_QUALITY_METRIC = """
    CAST(COUNT(CASE WHEN "{base_dist_column_name}_{dist}" IS NOT NULL AND "{base_dist_column_name}_{dist}" {dist_thresh_filter} AND "{base_dp_quality_col_name}_{dist}" IS NOT NULL AND "{base_dp_quality_col_name}_{dist}" {quality_thresh_filter} THEN 1 ELSE NULL END) AS DOUBLE) /
    COUNT(CASE WHEN ("{base_dist_column_name}_{dist}" IS NOT NULL) THEN 1 ELSE NULL END)
    AS "score_{ind}"
    """

DP_QUALITY_TRUE_REJECTION_METRIC = """
    CAST(COUNT(CASE WHEN "{base_dist_column_name}_{dist}" IS NOT NULL AND "{base_dist_column_name}_{dist}" {dist_thresh_filter} AND "{base_dp_quality_col_name}_{dist}" IS NOT NULL AND "{base_dp_quality_col_name}_{dist}" {quality_thresh_filter} THEN 1 ELSE NULL END) AS DOUBLE) /
    COUNT(CASE WHEN "{base_dist_column_name}_{dist}" IS NOT NULL AND "{base_dist_column_name}_{dist}" {dist_thresh_filter} THEN 1 ELSE NULL END)
    AS "score_{ind}"
    """


VIEW_RANGE_SUCCESS_RATE_QUERY = """
    SUM(CAST("{max_Z_col}_pred" >= {Z_sample} AND "{max_Z_col}_label" >= {Z_sample} AS DOUBLE)) / 
    SUM(CAST("{max_Z_col}_label" >= {Z_sample} AS DOUBLE))
    AS "vr_score_{Z_sample}"
    """

VIEW_RANGE_COUNT_GT_QUERY = """ SUM(CAST("{max_Z_col}_label" >= {Z_sample} AS DOUBLE)) AS "vr_num_gt_{Z_sample}" """

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
    AS "overall_{ind}"
    """

COUNT_ALL_METRIC = """
    COUNT(*)
    AS {count_name}
    """

EXTRACT_EVENT_ACC = """
    {dist_column} IS NOT NULL AND 
    {dist_column} {operator} {dist_thresh} AND 
    bin_population = '{chosen_source}'
"""

EXTRACT_EVENT_QUERY = """
    SELECT {final_columns} 
    FROM ({base_query}) 
    {order_cmd}
"""

SUM_SUCCESS_RATE_METRIC = """
    CAST(SUM(CASE WHEN {extra_filters} THEN {pred} ELSE 0 END) AS DOUBLE) / SUM(CASE WHEN {extra_filters} THEN {label} ELSE 0 END) 
    AS "score_{ind}"
    """

THRESHOLDS = np.concatenate(
    (np.array([-1000]), np.linspace(-5, -1, 5), np.linspace(-1, 2, 16), np.linspace(2, 6, 5), np.array([1000]))
)

PATHNET_ACC_THRESHOLDS = np.arange(0.2, 2, 0.05)

ROC_THRESHOLDS = np.concatenate(
    (
        np.array([-1000]),
        np.linspace(-10, -1, 10),
        np.linspace(-1 + 1 / 20, 1, 2 * 20),
        np.linspace(2, 10, 9),
        np.array([1000]),
    )
)

lm_3D_sec_to_Z_dist_acc = {0.5: 0.1, 1.0: 0.25, 1.3: 0.75, 1.5: 0.75, 2.0: 0.75, 2.5: 1.2, 3.0: 1.5}

lm_3D_sec_to_X_dist_acc = {0.5: 0.08, 1.0: 0.12, 1.3: 0.2, 1.5: 0.2, 2.0: 0.3, 2.5: 0.4, 3.0: 0.5}

lm_3d_distances = list(lm_3D_sec_to_X_dist_acc.keys())


class ZSources(str, enum.Enum):
    FUSION = "fusion"
    dZ = "dZ"
    dY = "dY"
    Z_COORDS = "Z_coords"


class Roles(str, enum.Enum):
    HOST = "host"
    NEXT = "next"
    OVERALL = ""


IGNORE_VALUE = 999
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
INTERSTING_FILTERS_DIST_TO_CHECK = 1.3


def generate_grab_index_hist_query(
    data_tables,
    meta_data,
    interesting_filters,
):
    base_query = generate_base_query(data_tables, meta_data)
    metrics = ", ".join(
        [
            COUNT_FILTER_METRIC.format(extra_filters=f"({filter})", ind=name)
            for name, filter in interesting_filters.items()
        ]
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
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
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=[col for col in [label_col, pred_col] if isinstance(col, str)],
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
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=[col for col in [label_col, pred_col] if isinstance(col, str)],
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    return query


def get_query_by_metrics(
    data_tables,
    meta_data,
    metrics,
    count_metrics=None,
    meta_data_filters="",
    extra_filters="",
    extra_columns=[],
    role="",
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=extra_columns,
        role=role,
    )

    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    if count_metrics is not None:
        metrics = format_metric_by_interesting_filters(count_metrics, MD_FILTER_COUNT)
        group_by = "net_id"
        md_count_query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by=group_by)
        query = JOIN_QUERY.format(t1=md_count_query, t2=query, col="net_id")
    return query


def generate_compare_metric_query(
    data_tables,
    meta_data,
    label_col,
    pred_col,
    interesting_filters,
    meta_data_filters="",
    extra_filters="",
    compare_operator=">=",
    extra_columns=[],
    role="",
):
    metrics = ", ".join(
        COMPARE_METRIC.format(
            label_col=label_col, operator=compare_operator, pred_col=pred_col, extra_filters=f"AND ({filter})", ind=name
        )
        for name, filter in interesting_filters.items()
    )
    count_metrics = get_compare_count_metrics(label_col, pred_col, interesting_filters, compare_operator)
    return get_query_by_metrics(
        data_tables,
        meta_data,
        metrics=metrics,
        count_metrics=count_metrics,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=[col for col in [label_col, pred_col] if isinstance(col, str)] + extra_columns,
        role=role,
    )


def generate_overall_stats_query(
    data_tables,
    meta_data,
    label_col,
    unavailable_value,
    threshold,
    meta_data_filters="",
    extra_filters="",
    base_extra_filters="",
    extra_columns=[],
    role="",
):
    COUNT_METRIC = """
        CAST(COUNT(CASE WHEN ({label_col} {operator} {pred_col}) {extra_filters} THEN 1 ELSE NULL END) AS DOUBLE) as count_{ind}"""
    metrics_list = []
    for metric in [COUNT_METRIC, COMPARE_METRIC]:
        metrics_list += [
            metric.format(
                label_col=label_col,
                operator="=",
                pred_col=unavailable_value,
                extra_filters=extra_filters,
                ind="unavailable",
            ),
            metric.format(
                label_col=label_col,
                operator="<=",
                pred_col=f"{threshold} AND {label_col} >= 0",
                extra_filters=f"OR {label_col} = -2 " + extra_filters,
                ind="accurate",
            ),
            metric.format(
                label_col=label_col,
                operator=">",
                pred_col=f"{threshold}",
                extra_filters=extra_filters,
                ind="inaccurate",
            ),
        ]
    metrics = ", ".join(metrics_list)
    return get_query_by_metrics(
        data_tables,
        meta_data,
        metrics=metrics,
        meta_data_filters=meta_data_filters,
        extra_filters=base_extra_filters,
        extra_columns=[label_col] + extra_columns,
        role=role,
    )


def generate_sum_success_rate_metric_query(
    data_tables,
    meta_data,
    label_col,
    pred_col,
    interesting_filters,
    meta_data_filters="",
    extra_filters="",
    extra_columns=[],
    role="",
):
    metrics = ", ".join(
        SUM_SUCCESS_RATE_METRIC.format(label=label_col, pred=pred_col, extra_filters=f"({filter})", ind=name)
        for name, filter in interesting_filters.items()
    )
    count_metrics = {
        interesting_filter_name: f"{extra_filters} AND {interesting_filter}"
        for interesting_filter_name, interesting_filter in interesting_filters.items()
    }
    return get_query_by_metrics(
        data_tables,
        meta_data,
        metrics=metrics,
        count_metrics=count_metrics,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=[col for col in [label_col, pred_col] if isinstance(col, str)] + extra_columns,
        role=role,
    )


def generate_sum_success_rate_metric_by_Z_bins_query(
    data_tables,
    meta_data,
    labels_to_preds,
    meta_data_filters="",
    extra_filters="",
    extra_columns=[],
    role="",
):
    metrics = ", ".join(
        SUM_SUCCESS_RATE_METRIC.format(
            label=label, pred=pred, extra_filters=" AND ".join([f"{l} >= 0" for l in label.split("+")]), ind=name
        )
        for name, (label, pred) in labels_to_preds.items()
    )
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=extra_columns
        + [
            col
            for name, label_to_pred in labels_to_preds.items()
            for cols_sum in label_to_pred
            for col in cols_sum.split("+")
        ],
        role=role,
    )

    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")

    SUM_METRIC = """
        CAST(SUM(CASE WHEN {extra_filters} THEN {col} ELSE 0 END) AS DOUBLE)
        AS "count_{ind}"
        """
    metrics = ", ".join(
        [
            SUM_METRIC.format(col=label, ind=name, extra_filters=" AND ".join([f"{l} >= 0" for l in label.split("+")]))
            for name, (label, pred) in labels_to_preds.items()
        ]
    )
    group_by = "net_id"
    md_count_query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by=group_by)
    query = JOIN_QUERY.format(t1=md_count_query, t2=query, col="net_id")
    return query


def generate_sum_bins_metric_query(
    data_tables,
    meta_data,
    sum_col,
    interesting_filters,
    meta_data_filters="",
    extra_filters="",
    extra_columns=[],
    role="",
):
    metrics = ", ".join(
        SUM_BY_CASE_METRIC.format(col_name=sum_col, extra_filters=filter, ind=name)
        for name, filter in interesting_filters.items()
    )
    count_metrics = {
        interesting_filter_name: f"{extra_filters} AND {interesting_filter}"
        for interesting_filter_name, interesting_filter in interesting_filters.items()
    }
    return get_query_by_metrics(
        data_tables,
        meta_data,
        metrics=metrics,
        count_metrics=count_metrics,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=[sum_col] + extra_columns,
        role=role,
    )


def generate_sum_bins_by_diff_cols_metric_query(
    data_tables,
    meta_data,
    labels_to_preds,
    meta_data_filters="",
    extra_filters="",
    extra_columns=[],
    role="",
):
    metrics = ", ".join(
        SUM_BY_CASE_METRIC.format(col_name=pred, extra_filters=f"{pred} >= 0 AND {pred} < {IGNORE_VALUE}", ind=name)
        for name, (label, pred) in labels_to_preds.items()
    )

    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=extra_columns + [col for name, label_to_pred in labels_to_preds.items() for col in label_to_pred],
        role=role,
    )

    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")

    SUM_METRIC = """
            CAST(SUM(CASE WHEN {extra_filters} THEN "{col}" ELSE 0 END) AS DOUBLE)
            AS "count_{ind}"
            """
    metrics = ", ".join(
        [
            SUM_METRIC.format(col=label, ind=name, extra_filters=f"{label} >= 0 AND {label} < {IGNORE_VALUE}")
            for name, (label, pred) in labels_to_preds.items()
        ]
    )
    group_by = "net_id"
    md_count_query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by=group_by)
    query = JOIN_QUERY.format(t1=md_count_query, t2=query, col="net_id")
    return query


def get_compare_count_metrics(label_col, pred_col, intresting_filters, operator):
    count_metrics = {}
    for extra_filter_name, extra_filter in intresting_filters.items():
        extra_filter_str = f"AND {extra_filter}" if extra_filter_name else ""
        count_metrics[extra_filter_name] = (
            f'"{label_col}" IS NOT NULL AND "{label_col}" {operator} {pred_col} {extra_filter_str}'
        )
    return count_metrics


def generate_avail_query(
    data_tables,
    meta_data,
    meta_data_filters="",
    extra_filters="",
    extra_columns=[],
    column_name="",
    role="",
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=extra_columns,
        role=role,
    )
    query = COLUMN_OPTION_QUERY.format(base_query=base_query, column_name=column_name)
    return query


def generate_path_net_query(
    data_tables,
    meta_data,
    distances_dict,
    meta_data_filters,
    extra_columns=["split_role", "matched_split_role", "ignore_role"],
    role="",
    extra_filters="",
):
    operator = "<"
    query = get_dist_query(
        "dist",
        data_tables,
        distances_dict,
        meta_data,
        meta_data_filters,
        operator,
        role,
        extra_columns=extra_columns,
        base_extra_filters=extra_filters,
    )
    return query


def generate_path_net_dp_quality_query(
    data_tables,
    meta_data,
    meta_data_filters="",
    extra_columns=["split_role", "matched_split_role", "ignore_role"],
    role="",
    base_dists=[0.2, 0.5],
    acc_dist_operator="<",
    quality_operator=">",
    quality_thresh_filter=0.0,
):
    coef = np.polyfit([1.3, 3], base_dists, deg=1)
    threshold_polynomial = np.poly1d(coef)
    distances_dict = {sec: max(threshold_polynomial(sec), 0.2) for sec in distances}
    quality_cols = [f'"quality_score_{sec}"' for sec in distances]
    extra_columns = extra_columns + quality_cols

    query = get_quality_score_query(
        base_dist_column_name="dist",
        base_dp_quality_col_name="quality_score",
        data_tables=data_tables,
        distances_dict=distances_dict,
        meta_data=meta_data,
        meta_data_filters=meta_data_filters,
        role=role,
        extra_columns=extra_columns,
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=quality_thresh_filter,
    )
    return query


def generate_path_net_dp_quality_true_rejection_query(
    data_tables,
    meta_data,
    meta_data_filters="",
    extra_columns=["split_role", "matched_split_role", "ignore_role"],
    role="",
    acc_dist_operator=">",
    quality_operator=">",
    quality_thresh_filter=0.0,
):

    distances_dict = {sec: PATHNET_IGNORE for sec in distances}
    quality_cols = [f'"quality_score_{sec}"' for sec in distances]
    extra_columns = extra_columns + quality_cols

    query = get_quality_score_query_true_rejection(
        base_dist_column_name="dist",
        base_dp_quality_col_name="quality_score",
        data_tables=data_tables,
        distances_dict=distances_dict,
        meta_data=meta_data,
        meta_data_filters=meta_data_filters,
        role=role,
        extra_columns=extra_columns,
        acc_dist_operator=acc_dist_operator,
        quality_operator=quality_operator,
        quality_thresh_filter=quality_thresh_filter,
    )
    return query


def generate_path_net_miss_false_query(
    data_tables,
    meta_data,
    interesting_filters,
    meta_data_filters="",
    extra_columns=["split_role", "matched_split_role", "ignore_role"],
    role="",
    extra_filters="",
):
    query = get_dist_query(
        "dist",
        data_tables,
        {PATHNET_BASE_DIST: PATHNET_IGNORE},
        meta_data,
        meta_data_filters,
        ">",
        role,
        intresting_filters=interesting_filters,
        extra_columns=extra_columns,
        is_add_filters_count=True,
        base_extra_filters=extra_filters,
    )
    return query


def generate_extract_acc_events_query(
    data_tables,
    meta_data,
    meta_data_filters,
    bookmarks_columns,
    chosen_source,
    role,
    dist,
    threshold,
    operator,
    order_by,
):
    acc_columns = ["matched_dp_id", "dp_id", "match_score"]
    dist_column = f'"dist_{dist}"'
    acc_cmd = EXTRACT_EVENT_ACC.format(
        dist_column=f'"dist_{dist}"', operator=operator, dist_thresh=threshold, chosen_source=chosen_source
    )
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        role=role,
        extra_columns=acc_columns,
        extra_filters=acc_cmd,
    )
    final_columns = bookmarks_columns + acc_columns
    order_cmd = f"ORDER BY {dist_column} {order_by}"
    query = EXTRACT_EVENT_QUERY.format(
        final_columns=", ".join(final_columns + [dist_column]), base_query=base_query, order_cmd=order_cmd
    )
    return query, final_columns


def generate_extract_miss_false_events_query(
    data_tables, meta_data, meta_data_filters, bookmarks_columns, chosen_source, role
):
    metric_columns = ["dp_id"]
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        role=role,
        extra_columns=metric_columns,
        extra_filters=f"bin_population = '{chosen_source}'",
    )
    final_columns = bookmarks_columns + metric_columns
    query = EXTRACT_EVENT_QUERY.format(final_columns=", ".join(final_columns), base_query=base_query, order_cmd="")
    return query, final_columns


def generate_view_range_success_rate_query(
    data_tables,
    meta_data,
    Z_samples,
    meta_data_filters="",
    role="",
    naive_Z=False,
    use_err_est=True,
    err_est_threshold=0.2,
):
    max_Z_col = get_view_range_col_name("view_range_max_Z", naive_Z, use_err_est, err_est_threshold)
    metrics_lst = []
    for Z in Z_samples:
        metrics_lst.append(VIEW_RANGE_SUCCESS_RATE_QUERY.format(max_Z_col=max_Z_col, Z_sample=Z))
        metrics_lst.append(VIEW_RANGE_COUNT_GT_QUERY.format(max_Z_col=max_Z_col, Z_sample=Z))
    metrics = ", ".join(metrics_lst)
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters="confidence > 0 AND match <> -1",
        role=role,
        extra_columns=[f'"{max_Z_col}_pred"', f'"{max_Z_col}_label"'],
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")

    return query


def get_view_range_col_name(max_Z_col, naive_Z, use_err_est, threshold):
    if not naive_Z:
        max_Z_col += "_3d"
    if use_err_est:
        max_Z_col += f"_err_est_{threshold}"
    return max_Z_col


def generate_view_range_histogram_query(
    data_tables,
    meta_data,
    bin_size,
    meta_data_filters="",
    role="",
    naive_Z=False,
    use_err_est=True,
    err_est_threshold=0.2,
):
    max_Z_col = get_view_range_col_name("view_range_max_Z", naive_Z, use_err_est, err_est_threshold)
    query = generate_count_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        bins_factor=bin_size,
        extra_filters="confidence > 0 AND match <> -1",
        role=role,
        extra_columns=[f'"{max_Z_col}_pred"', f'"{max_Z_col}_label"'],
        group_by_column=f'"{max_Z_col}_pred"',
        group_by_net_id=True,
        include_all=False,
    )

    query = f'{query} ORDER BY net_id, "{max_Z_col}_pred"'

    return query


def generate_lm_3d_query(
    data_tables,
    meta_data,
    state,
    meta_data_filters="",
    role="",
    is_Z=False,
    intresting_filters=None,
    Z_source=ZSources.FUSION,
):
    operator = "<" if state == "accuracy" else ">"
    distances = lm_3D_sec_to_Z_dist_acc if is_Z else lm_3D_sec_to_X_dist_acc
    if intresting_filters is not None:
        distances = {INTERSTING_FILTERS_DIST_TO_CHECK: distances[INTERSTING_FILTERS_DIST_TO_CHECK]}
    axis = "Z" if is_Z else "X"
    base_column_name = f"pos_dZ_{Z_source}_{axis}_dists"
    query = get_dist_query(
        base_column_name,
        data_tables,
        distances,
        meta_data,
        meta_data_filters,
        operator,
        role,
        base_extra_filters="confidence > 0 AND match <> -1",
        is_add_filters_count=True,
        intresting_filters=intresting_filters,
        extra_filters=f'AND ("{base_column_name}_{{dist}}" < 999)',
    )
    return query


def get_dist_query(
    base_dist_column_name,
    data_tables,
    distances_dict,
    meta_data,
    meta_data_filters,
    operator,
    role,
    base_extra_filters="",
    is_add_filters_count=False,
    intresting_filters=None,
    extra_columns=None,
    extra_filters="",
):
    if intresting_filters is None:
        intresting_filters = {"": ""}
    metrics = ", ".join(
        DIST_METRIC.format(
            thresh_filter=f"{operator} {thresh}",
            dist=sec,
            extra_filters=(
                f"{extra_filters.format(dist=sec)} AND {intresting_filter}"
                if intresting_filter_name
                else extra_filters.format(dist=sec)
            ),
            base_dist_column_name=base_dist_column_name,
            ind=intresting_filter_name if intresting_filter_name else sec,
        )
        for sec, thresh in distances_dict.items()
        for intresting_filter_name, intresting_filter in intresting_filters.items()
    )
    count_metrics = (
        get_dist_count_metrics(base_dist_column_name, distances_dict, intresting_filters, operator)
        if is_add_filters_count
        else None
    )
    return get_query_by_metrics(
        data_tables,
        meta_data,
        metrics,
        count_metrics=count_metrics,
        meta_data_filters=meta_data_filters,
        extra_filters=base_extra_filters,
        role=role,
        extra_columns=extra_columns,
    )


def get_dist_count_metrics(base_dist_column_name, distances_dict, intresting_filters, operator):
    count_metrics = {}
    for sec, thresh in distances_dict.items():
        for extra_filter_name, extra_filter in intresting_filters.items():
            filter_name = extra_filter_name if extra_filter_name else f"{sec}"
            extra_filter_str = f"AND {extra_filter}" if extra_filter_name else ""
            count_metrics[filter_name] = (
                f'"{base_dist_column_name}_{sec}" IS NOT NULL AND "{base_dist_column_name}_{sec}" {operator} {thresh} {extra_filter_str}'
            )
    return count_metrics


def generate_emdp_view_range_Z_histogram_query(
    data_tables, meta_data, bin_size, meta_data_filters="", role="", naive_Z=False, use_monotonic=True
):
    max_Z_col = "max_Z"
    max_Z_col = _get_emdp_col(max_Z_col, naive_Z, use_monotonic)
    query = generate_count_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        bins_factor=bin_size,
        role=role,
        extra_columns=[max_Z_col],
        group_by_column=max_Z_col,
        group_by_net_id=True,
        include_all=False,
    )

    query = f"{query} ORDER BY net_id, {max_Z_col}"

    return query


def generate_emdp_view_range_sec_histogram_query(
    data_tables, meta_data, meta_data_filters="", role="", naive_Z=False, use_monotonic=True, extra_filters=""
):
    VIEW_RANGE_SEC = [0.5 * x for x in range(0, 11)]
    max_Z_cols = [f"Z_{sec}" for sec in VIEW_RANGE_SEC]
    max_Z_cols = [_get_emdp_col(col, naive_Z, use_monotonic) for col in max_Z_cols]
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        extra_columns=[f'"{col}"' for col in max_Z_cols],
        role=role,
    )
    metrics = ", ".join(
        COUNT_FILTER_METRIC.format(extra_filters=f'"{label_col}" = 1', ind=label_col) for label_col in max_Z_cols
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")

    return query


def _get_emdp_col(max_Z_col, naive_Z, use_monotonic):
    if use_monotonic:
        max_Z_col += "_monotonic"
    if not naive_Z:
        max_Z_col += "_world"
    return max_Z_col


def generate_fb_query(
    gt_data_tables,
    pred_data_tables,
    meta_data,
    interesting_filters={},
    input_thresh={},
    meta_data_filters="",
    extra_filters="",
    role="",
):
    recall_query = generate_recall_query(
        gt_data_tables,
        meta_data,
        interesting_filters=interesting_filters,
        input_thresh=input_thresh,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        role=role,
    )

    precision_filter = "match_score >= 0"
    precision_query = generate_precision_query(
        pred_data_tables,
        meta_data,
        interesting_filters=interesting_filters,
        input_thresh=input_thresh,
        meta_data_filters=meta_data_filters,
        extra_filters=precision_filter if not extra_filters else f"{extra_filters} AND {precision_filter}",
        role=role,
    )

    final_query = JOIN_QUERY.format(t1=recall_query, t2=precision_query, col="net_id")
    return final_query


def generate_precision_query(
    data_tables,
    meta_data,
    interesting_filters={},
    input_thresh={},
    meta_data_filters="",
    extra_filters="",
    role="",
):
    metrics = (
        format_metric_by_interesting_filters(interesting_filters, FB_PRECISION_METRIC)
        if interesting_filters
        else get_fb_curve_metrics(FB_PRECISION_METRIC)
    )
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        role=role,
    )
    group_by = get_fb_group_by(input_thresh)
    final_query = DYNAMIC_METRICS_QUERY.format(
        metrics=metrics, base_query=base_query, group_by=group_by if interesting_filters else "net_id"
    )
    return final_query


def generate_pathnet_cumulative_query(
    data_tables,
    meta_data,
    column,
    meta_data_filters="",
    extra_filters="",
    extra_columns=["split_role", "matched_split_role", "ignore_role"],
    role="",
):
    metrics = ", ".join(
        PATHNET_THRESHOLD_METRIC.format(column=column, threshold=thresh, ind=ind)
        for ind, thresh in enumerate(PATHNET_ACC_THRESHOLDS)
    )
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_columns=extra_columns,
        extra_filters=extra_filters,
        role=role,
    )

    final_query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    return final_query


def generate_recall_query(
    data_tables,
    meta_data,
    interesting_filters={},
    input_thresh={},
    meta_data_filters="",
    extra_filters="",
    role="",
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        role=role,
    )
    metrics = (
        format_metric_by_interesting_filters(interesting_filters, FB_OVERALL_METRIC)
        if interesting_filters
        else get_fb_curve_metrics(FB_CURVE_METRIC)
    )
    recall_query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    if not interesting_filters:
        return recall_query

    metrics = format_metric_by_interesting_filters(interesting_filters, MD_FILTER_COUNT)
    group_by = get_fb_group_by(input_thresh)
    md_count_query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by=group_by)

    final_query = JOIN_QUERY.format(t1=md_count_query, t2=recall_query, col="net_id")
    return final_query


def format_metric_by_interesting_filters(interesting_filters, metric):
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
    role="",
    ca_oriented=False,
    compare_sign=False,
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        extra_columns=[col for col in [label_col, pred_col] if isinstance(col, str)],
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        role=role,
        ca_oriented=ca_oriented,
    )
    group_by_label = f"(CASE WHEN {label_col} >= 0 THEN 1 ELSE -1 END)" if compare_sign else label_col
    group_by_pred = f"(CASE WHEN {pred_col} >= 0 THEN 1 ELSE -1 END)" if compare_sign else pred_col
    conf_query = CONF_MAT_QUERY.format(
        group_by_label=group_by_label,
        group_by_pred=group_by_pred,
        label_col=label_col,
        pred_col=pred_col,
        base_query=base_query,
        count_name="res_count",
    )
    return conf_query


def generate_count_query(
    data_tables,
    meta_data,
    group_by_column="net_id",
    meta_data_filters="",
    extra_filters="",
    bins_factor=None,
    role="",
    include_all=True,
    extra_columns=None,
    group_by_net_id=False,
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
        role=role,
        include_all=include_all,
        extra_columns=extra_columns,
    )
    metrics = COUNT_ALL_METRIC.format(count_name="overall")
    group_by = f"FLOOR({group_by_column} / {bins_factor}) * {bins_factor}" if bins_factor else group_by_column
    if group_by_net_id:
        group_by = "net_id, " + group_by
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
    role="",
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
        role=role,
        include_all=True,
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
    role="",
    ca_oriented=False,
    compare_sign=False,
    compare_operator="=",
):
    base_query = generate_base_query(
        data_tables,
        meta_data,
        extra_columns=[col for col in [label_col, pred_col] if isinstance(col, str)],
        meta_data_filters=meta_data_filters,
        ca_oriented=ca_oriented,
        role=role,
        extra_filters=extra_filters,
    )
    label_col = f"(CASE WHEN {label_col} >= 0 THEN 1 ELSE -1 END)" if compare_sign else label_col
    pred_col = f"(CASE WHEN {pred_col} >= 0 THEN 1 ELSE -1 END)" if compare_sign else pred_col
    compare_query = COMPARE_QUERY.format(
        label_col=label_col, pred_col=pred_col, base_query=base_query, operator=compare_operator
    )
    return compare_query


def generate_roc_query(
    data_tables,
    meta_data,
    label_col=None,
    pred_col=None,
    interesting_filters={},
    input_thresh={},
    thresholds=ROC_THRESHOLDS,
    meta_data_filters="",
    extra_filters="",
    role="",
):
    assert label_col is not None
    assert pred_col is not None

    metrics = (
        get_roc_stats_per_filter_metrics(
            label_col, pred_col, interesting_filters, ROC_STATS_METRIC, threshold=input_thresh
        )
        if interesting_filters
        else get_roc_stats_curve_metrics(label_col, pred_col, ROC_STATS_METRIC, thresholds=thresholds)
    )
    extra_columns = [label_col, pred_col]
    base_query = generate_base_query(
        data_tables,
        meta_data,
        meta_data_filters=meta_data_filters,
        extra_columns=extra_columns,
        extra_filters=extra_filters,
        role=role,
    )
    group_by = get_roc_group_by(label_col, pred_col, input_thresh)
    final_query = DYNAMIC_METRICS_QUERY.format(
        metrics=metrics, base_query=base_query, group_by=group_by if interesting_filters else "net_id"
    )
    return final_query


def get_roc_stats_per_filter_metrics(label_col, pred_col, interesting_filters, metric, threshold=0):
    metrics = ", ".join(
        metric.format(
            label_col=label_col, pred_col=pred_col, extra_filters=f"AND ({filter})", threshold=threshold, ind=name
        )
        for name, filter in interesting_filters.items()
    )
    return metrics


def get_roc_stats_curve_metrics(label_col, pred_col, metric, thresholds=ROC_THRESHOLDS):
    metrics = ", ".join(
        metric.format(label_col=label_col, pred_col=pred_col, extra_filters="", ind=ind, threshold=threshold)
        for ind, threshold in enumerate(thresholds)
    )
    return metrics


def get_roc_group_by(label_col, pred_col, input_thresh={}):
    if not input_thresh:
        group_by = "net_id"
        return group_by

    cases = "\n".join(
        f"WHEN net_id = '{net_id}' AND {pred_col} >= {thresh} THEN '{net_id}'"
        for net_id, thresh in input_thresh.items()
    )
    group_by = f"CASE {cases} END"
    return group_by


def generate_cols_query(data_tables, search_string):
    paths = ",".join(f"'{path}'" for path in data_tables["paths"])
    cols_query = COLS_QUERY.format(paths=paths, search_string=search_string)
    return cols_query


def generate_base_query(
    data_tables,
    meta_data,
    meta_data_filters="",
    include_all=False,
    ca_oriented=False,
    role="",
    extra_filters="",
    extra_columns=None,
):
    if extra_columns is None:
        extra_columns = []
    base_data = generate_base_data(data_tables["paths"], data_tables["required_columns"], extra_columns)
    intersect_filter = generate_intersect_filter(data_tables["paths"])
    ignore_str = data_tables["ca_ignore_filter"] if ca_oriented else data_tables["ignore_filter"]
    stats_filters = generate_stats_filters(ignore_str, include_all, ca_oriented, role, extra_filters)
    meta_data_filters = "AND " + meta_data_filters if meta_data_filters else ""
    base_query = BASE_QUERY.format(
        base_data=base_data,
        meta_data=meta_data,
        meta_data_filters=meta_data_filters,
        intersect_filter=intersect_filter,
        stats_filters=stats_filters,
    )
    return base_query


def generate_base_data(data_paths, base_columns, extra_columns=[]):
    data_columns = ", ".join(base_columns + extra_columns)
    union_str = f" UNION ALL SELECT {data_columns} FROM ".join(data_paths)
    return f"SELECT {data_columns} FROM {union_str}"


def generate_stats_filters(
    filter_str,
    include_all=False,
    ca_oriented=False,
    role="",
    extra_filters="",
):
    ignore_string = "" if include_all else filter_str
    role_col = "ca_role" if ca_oriented else "role"
    role_string = f"{role_col} = '{role}'" if role else ""
    if type(role) == list:
        role_string = f"({role_col} = {f' OR {role_col}='.join(role)})"

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
        df = df.sort_values(nets_names_col)
    return df


def process_net_names_list(net_names):
    return sorted([process_net_name(net_name) for net_name in net_names], reverse=True)


def process_net_name(net_name):
    if pd.isnull(net_name):
        return net_name
    return re.sub(r"(^\d{18}-)|(_default$)|(_$)", "", net_name)


def get_quality_score_query(
    base_dist_column_name,
    base_dp_quality_col_name,
    data_tables,
    distances_dict,
    meta_data,
    meta_data_filters,
    role,
    intresting_filters=None,
    extra_columns=None,
    quality_thresh_filter=0.0,
    acc_dist_operator="<",
    quality_operator=">",
):
    if intresting_filters is None:
        intresting_filters = {"": ""}
    metrics = ", ".join(
        DP_QUALITY_METRIC.format(
            dist_thresh_filter=f"{acc_dist_operator} {thresh}",
            dist=sec,
            base_dist_column_name=base_dist_column_name,
            base_dp_quality_col_name=base_dp_quality_col_name,
            quality_thresh_filter=f"{quality_operator} {quality_thresh_filter}",
            ind=intresting_filter_name if intresting_filter_name else sec,
        )
        for sec, thresh in distances_dict.items()
        for intresting_filter_name, intresting_filter in intresting_filters.items()
    )
    return get_query_by_metrics(
        data_tables,
        meta_data,
        metrics,
        count_metrics=None,
        meta_data_filters=meta_data_filters,
        extra_filters="",
        role=role,
        extra_columns=extra_columns,
    )


def get_quality_score_query_true_rejection(
    base_dist_column_name,
    base_dp_quality_col_name,
    data_tables,
    distances_dict,
    meta_data,
    meta_data_filters,
    role,
    extra_columns=None,
    quality_thresh_filter=0.0,
    acc_dist_operator="<",
    quality_operator=">",
):

    metrics = ", ".join(
        DP_QUALITY_TRUE_REJECTION_METRIC.format(
            dist_thresh_filter=f"{acc_dist_operator} {thresh}",
            dist=sec,
            base_dist_column_name=base_dist_column_name,
            base_dp_quality_col_name=base_dp_quality_col_name,
            quality_thresh_filter=f"{quality_operator} {quality_thresh_filter}",
            ind=sec,
        )
        for sec, thresh in distances_dict.items()
    )
    return get_query_by_metrics(
        data_tables,
        meta_data,
        metrics,
        count_metrics=None,
        meta_data_filters=meta_data_filters,
        extra_filters="",
        role=role,
        extra_columns=extra_columns,
    )
