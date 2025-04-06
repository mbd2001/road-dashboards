import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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


def create_quality_view_range_histogram(df: pd.DataFrame, role: str, bin_size: int = 10) -> go.Figure:
    """
    Create a line graph showing distribution of quality view range values
    where each point represents percentage of paths with view_range >= bin value.

    NOTICE: The value of the view range is not configurable, it is a constant value (quality_view_range) that is
    set at pathnet Stats based on threshold of 0.5.

    Args:
        df: DataFrame with quality_view_range and overall (count) columns
        role: Role type (host or non-host)
        bin_size: Size of bins in meters

    Returns:
        A plotly line graph figure
    """
    column_name = DPQualityQueryConfig.quality_view_range_column_name

    if df.empty or column_name not in df.columns:
        return go.Figure()

    df = df[df[column_name].notna()]

    if df.empty:
        return go.Figure()

    result_data = []

    overall_max = df[column_name].max()

    min_bin = 0
    max_bin = ((overall_max // bin_size) + 1) * bin_size
    all_bins = np.arange(min_bin, max_bin, bin_size)

    for net_id in df["net_id"].unique():
        net_df = df[df["net_id"] == net_id]

        if not net_df.empty:
            total_count = net_df["overall"].sum()

            for bin_value in all_bins:
                count = net_df[net_df[column_name] >= bin_value]["overall"].sum()
                percentage = count / total_count if total_count > 0 else 0
                result_data.append({"bin": bin_value, "percentage": percentage, "count": count, "net_id": net_id})

    hist_df = pd.DataFrame(result_data)

    hist_df.sort_values(by=["net_id", "bin"], inplace=True)

    title = f"Quality View Range Distribution ({role})"

    fig = px.line(
        hist_df,
        x="bin",
        y="percentage",
        color="net_id",
        markers=True,
        hover_data={"bin": True, "net_id": False, "percentage": ":.2%", "count": True},
        labels={"bin": "View Range (m)", "percentage": "Percentage", "count": "Count"},
    )

    fig.update_layout(
        title=title,
        xaxis_title="View Range (m)",
        yaxis_title="Percentage",
        xaxis=dict(range=[-5, max_bin], constrain="domain", title_standoff=25),
        yaxis=dict(range=[0, 1.1], tickformat=".0%"),
        font=dict(size=16),
        hoverlabel=dict(font_size=16),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5,
            title=None,
        ),
        margin=dict(b=120),
    )

    return fig
