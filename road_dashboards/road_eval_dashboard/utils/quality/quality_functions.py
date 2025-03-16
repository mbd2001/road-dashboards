import pandas as pd

from road_dashboards.road_eval_dashboard.utils.distances import SECONDS
from road_dashboards.road_eval_dashboard.utils.quality.quality_config import DPQualityQueryConfig, MetricType

IGNORE_VALUES = [999, -999, 990]

TP_PREFIX = "tp"
FP_PREFIX = "fp"
FN_PREFIX = "fn"
TN_PREFIX = "tn"

COUNT_METRIC_TEMPLATE = "SUM(CASE WHEN {condition} THEN 1 ELSE 0 END) AS {alias}"


def get_counts_expressions_for_sec(config: DPQualityQueryConfig, sec: float, dist_thresh: float) -> dict:
    """
    Build count expressions for TP, FP, FN, and TN for a given second.
    """
    dist_col = f'"{config.base_dist_column_name}_{sec}"'
    quality_col = f'"{config.base_dp_quality_col_name}_{sec}"'

    ignore_values_str = ", ".join(map(str, IGNORE_VALUES))

    valid_rows = (
        f"{dist_col} IS NOT NULL AND {dist_col} NOT IN ({ignore_values_str}) AND "
        f"{quality_col} IS NOT NULL AND {quality_col} NOT IN ({ignore_values_str})"
    )

    positive_gt = f"({valid_rows} AND {dist_col} <= {dist_thresh})"
    negative_gt = f"({valid_rows} AND {dist_col} > {dist_thresh})"
    positive_pred = f"({valid_rows} AND {quality_col} >= {config.quality_prob_score_thresh})"
    negative_pred = f"({valid_rows} AND {quality_col} < {config.quality_prob_score_thresh})"

    tp_expr = COUNT_METRIC_TEMPLATE.format(
        condition=f"({positive_gt} AND {positive_pred})", alias=f'"{TP_PREFIX}_{sec}"'
    )
    fp_expr = COUNT_METRIC_TEMPLATE.format(
        condition=f"({negative_gt} AND {positive_pred})", alias=f'"{FP_PREFIX}_{sec}"'
    )
    fn_expr = COUNT_METRIC_TEMPLATE.format(
        condition=f"({positive_gt} AND {negative_pred})", alias=f'"{FN_PREFIX}_{sec}"'
    )
    tn_expr = COUNT_METRIC_TEMPLATE.format(
        condition=f"({negative_gt} AND {negative_pred})", alias=f'"{TN_PREFIX}_{sec}"'
    )

    return {TP_PREFIX: tp_expr, FP_PREFIX: fp_expr, FN_PREFIX: fn_expr, TN_PREFIX: tn_expr}


def compute_metrics_from_count_df(df: pd.DataFrame) -> dict:
    """
    Given a DataFrame with aggregated counts (tp_<sec>, fp_<sec>, fn_<sec>, tn_<sec>),
    compute quality metrics (Correct Acceptance Rate, Incorrect Acceptance Rate, Correct Rejection Rate, Incorrect Rejection Rate, Accuracy, Precision).

    Returns a dictionary of DataFrames, one for each metric, with seconds as columns.
    """
    metric_dfs = {}
    for sec in SECONDS:
        tp = df[f"{TP_PREFIX}_{sec}"]
        fp = df[f"{FP_PREFIX}_{sec}"]
        fn = df[f"{FN_PREFIX}_{sec}"]
        tn = df[f"{TN_PREFIX}_{sec}"]

        total = tp + fp + fn + tn

        metrics = {
            MetricType.CORRECT_ACCEPTANCE_RATE: tp / (tp + fn),  # True Positive Rate (Recall)
            MetricType.INCORRECT_ACCEPTANCE_RATE: fp / (fp + tn),  # False Positive Rate
            MetricType.CORRECT_REJECTION_RATE: tn / (tn + fp),  # True Negative Rate
            MetricType.INCORRECT_REJECTION_RATE: fn / (tp + fn),  # False Negative Rate
            MetricType.ACCURACY: (tp + tn) / total,  # Accuracy
            MetricType.PRECISION: tp / (tp + fp),  # Precision
        }

        for metric, series in metrics.items():
            if metric not in metric_dfs:
                metric_dfs[metric] = pd.DataFrame(index=df.index)
            metric_dfs[metric][sec] = series

    for metric_df in metric_dfs.values():
        metric_df["net_id"] = df["net_id"].values

    return metric_dfs
