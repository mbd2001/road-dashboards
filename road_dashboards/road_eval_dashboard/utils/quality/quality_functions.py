from road_dashboards.road_eval_dashboard.utils.quality.quality_config import (
    QUALITY_METRIC_TEMPLATE,
    DPQualityQueryConfig,
    MetricType,
)


def get_quality_metric_query(metric: MetricType, config: DPQualityQueryConfig, sec: float, dist_thresh: float) -> str:
    """
    Given a MetricType, return the full metric query string.

    Prediction is positive when quality score > threshold
    Ground truth is positive when distance < threshold
    """

    positive_gt = (
        f'"{config.base_dist_column_name}_{sec}" IS NOT NULL AND "{config.base_dist_column_name}_{sec}" < {dist_thresh}'
    )
    negative_gt = f'"{config.base_dist_column_name}_{sec}" IS NOT NULL AND "{config.base_dist_column_name}_{sec}" >= {dist_thresh}'

    positive_pred = f'"{config.base_dp_quality_col_name}_{sec}" IS NOT NULL AND "{config.base_dp_quality_col_name}_{sec}" > {config.quality_prob_score_thresh}'
    negative_pred = f'"{config.base_dp_quality_col_name}_{sec}" IS NOT NULL AND "{config.base_dp_quality_col_name}_{sec}" <= {config.quality_prob_score_thresh}'

    tp = f"({positive_gt} AND {positive_pred})"  # Correct Acceptance
    fp = f"({negative_gt} AND {positive_pred})"  # Incorrect Acceptance
    fn = f"({positive_gt} AND {negative_pred})"  # Incorrect Rejection
    tn = f"({negative_gt} AND {negative_pred})"  # Correct Rejection

    match metric:
        case MetricType.CORRECT_ACCEPTANCE_RATE:
            num_condition = tp
            denom_condition = positive_gt

        case MetricType.INCORRECT_ACCEPTANCE_RATE:
            num_condition = fp
            denom_condition = negative_gt

        case MetricType.INCORRECT_REJECTION_RATE:
            num_condition = fn
            denom_condition = positive_gt

        case MetricType.CORRECT_REJECTION_RATE:
            num_condition = tn
            denom_condition = negative_gt

        case MetricType.ACCURACY:
            num_condition = f"({tp}) OR ({tn})"
            denom_condition = f"({positive_gt}) OR ({negative_gt})"

        case MetricType.PRECISION:
            num_condition = tp
            denom_condition = positive_pred

        case _:
            raise ValueError("Unsupported metric type")

    return QUALITY_METRIC_TEMPLATE.format(num_condition=num_condition, denom_condition=denom_condition, ind=sec)
