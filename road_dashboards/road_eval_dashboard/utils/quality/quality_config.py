from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from road_dashboards.road_eval_dashboard.utils.colors import GREEN, RED

# SAME AS maffe_bins/utils/perfects/pathnet/pw_bins_creator_consts.py
POINTS_PER_PATH_OG = 18
FIRST_SAMPLING_Z = 6.5
SAMPLING_POINTS_OG = FIRST_SAMPLING_Z + np.cumsum(np.arange(POINTS_PER_PATH_OG))
SAMPLING_POINTS = np.sort(np.concatenate((SAMPLING_POINTS_OG, SAMPLING_POINTS_OG[15] + np.arange(15, 76, 15))))
ATTN_NUM_POINTS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 21, 22]

SELECTED_SAMPLING_POINTS = SAMPLING_POINTS[ATTN_NUM_POINTS]


@dataclass
class DPQualityQueryConfig:
    data_tables: Any
    meta_data: Any
    meta_data_filters: str = ""
    role: str = ""
    extra_columns: list[str] = field(default_factory=lambda: ["split_role", "matched_split_role", "ignore_role"])
    base_dist_column_name: str = "dist"
    base_dp_quality_col_name: str = "quality_probs"
    quality_view_range_column_name: str = "quality_view_range"
    quality_prob_score_thresh: float = 0.5  # Probability of the predicted point is correct


class MetricType(str, Enum):
    """
    Enum that defines the type of metric to be used in the query.

    Attributes:
        CORRECT_ACCEPTANCE_RATE: Correct Acceptance Rate (tp / (tp + fn))
        INCORRECT_ACCEPTANCE_RATE: Incorrect Acceptance Rate (fp / (fp + tn))
        CORRECT_REJECTION_RATE: Correct Rejection Rate (tn / (tp + fn))
        INCORRECT_REJECTION_RATE: Incorrect Rejection Rate (fn / (tp + fn))
        ACCURACY: Accuracy ((tp + tn) / (tp + fp + fn + tn))
        PRECISION: Precision (tp / (tp + fp))
    """

    CORRECT_ACCEPTANCE_RATE = "Correct Acceptance Rate"
    INCORRECT_ACCEPTANCE_RATE = "Incorrect Acceptance Rate"
    CORRECT_REJECTION_RATE = "Correct Rejection Rate"
    INCORRECT_REJECTION_RATE = "Incorrect Rejection Rate"
    ACCURACY = "Accuracy"
    PRECISION = "Precision"


METRIC_GRAPHS_SETTINGS = {
    MetricType.CORRECT_ACCEPTANCE_RATE: {
        "title": "Correct Acceptance Rate",
        "yaxis": "Correct Acceptance Rate (%)",
        "bg": GREEN,
    },
    MetricType.INCORRECT_ACCEPTANCE_RATE: {
        "title": "Incorrect Acceptance Rate",
        "yaxis": "Incorrect Acceptance Rate (%)",
        "bg": RED,
    },
    MetricType.CORRECT_REJECTION_RATE: {
        "title": "Correct Rejection Rate",
        "yaxis": "Correct Rejection Rate (%)",
        "bg": GREEN,
    },
    MetricType.INCORRECT_REJECTION_RATE: {
        "title": "Incorrect Rejection Rate",
        "yaxis": "Incorrect Rejection Rate (%)",
        "bg": RED,
    },
    MetricType.ACCURACY: {"title": "Accuracy", "yaxis": "Accuracy (%)", "bg": GREEN},
    MetricType.PRECISION: {"title": "Precision", "yaxis": "Precision (%)", "bg": GREEN},
}


def compute_fixed_thresholds(
    distances: np.ndarray = SELECTED_SAMPLING_POINTS,
    start_threshold: float = 0.4,
    slope: float = 0.01,  # Threshold increase per unit distance (e.g., 0.01 means 1cm per 1m)
    upper_bound: float = 1.2,
) -> np.ndarray:
    """
    Computes thresholds that increase linearly with distance based on a fixed slope.

    The threshold starts at `start_threshold` for the minimum distance and increases
    by `slope` for each unit increase in distance relative to the minimum distance.
    The final threshold value is clamped at `upper_bound`.

    Args:
        distances: A numpy array of distances.
        start_threshold: The threshold value corresponding to the minimum distance.
        slope: The rate at which the threshold increases per unit of distance.
        upper_bound: The absolute maximum value allowed for the threshold (clamping value).

    Returns:
        A list of computed linear thresholds, clamped at `upper_bound`.
    """
    if distances.size == 0:
        return []
    min_dist = np.min(distances)
    linear_thresholds = start_threshold + (distances - min_dist) * slope
    final_thresholds = np.minimum(linear_thresholds, upper_bound)
    return final_thresholds.tolist()


def get_hover_text_parts(metric_type: MetricType, tp: int, fn: int, fp: int, tn: int) -> list[str]:
    """
    Generates a list of strings for hover text based on the metric type and confusion matrix values.
    """
    hover_parts = []
    match metric_type:
        case MetricType.CORRECT_ACCEPTANCE_RATE:
            total_p = tp + fn
            hover_parts.extend([f"TP: {tp}, FN: {fn}", f"Actual Positives: {total_p}"])
        case MetricType.INCORRECT_ACCEPTANCE_RATE:
            total_n = fp + tn
            hover_parts.extend([f"FP: {fp}, TN: {tn}", f"Actual Negatives: {total_n}"])
        case MetricType.CORRECT_REJECTION_RATE:
            total_n = tn + fp
            hover_parts.extend([f"TN: {tn}, FP: {fp}", f"Actual Negatives: {total_n}"])
        case MetricType.INCORRECT_REJECTION_RATE:
            total_p = fn + tp
            hover_parts.extend([f"FN: {fn}, TP: {tp}", f"Actual Positives: {total_p}"])
        case MetricType.ACCURACY:
            total_samples = tp + tn + fp + fn
            hover_parts.extend([f"TP: {tp}, TN: {tn}", f"FP: {fp}, FN: {fn}", f"Total Samples: {total_samples}"])
        case MetricType.PRECISION:
            total_pred_p = tp + fp
            hover_parts.extend([f"TP: {tp}, FP: {fp}", f"Predicted Positives: {total_pred_p}"])
        case _:
            hover_parts.append("Counts: N/A")
    return hover_parts
