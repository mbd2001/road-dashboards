from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass
class DPQualityQueryConfig:
    data_tables: Any
    meta_data: Any
    meta_data_filters: str = ""
    role: str = ""
    extra_columns: list[str] = field(default_factory=lambda: ["split_role", "matched_split_role", "ignore_role"])
    base_dist_column_name: str = "dist"
    base_dp_quality_col_name: str = "quality_score"
    quality_prob_score_thresh: float = 0.5  # Probability of the predicted point is correct


class MetricType(str, Enum):
    """
    Enum that defines the type of metric to be used in the query.

    Attributes:
        TPR: True Positive Rate (tp / (tp + fn))
        FPR: False Positive Rate (fp / (fp + tn))
        TNR: True Negative Rate (tn / (tp + fn))
        FNR: False Negative Rate (fn / (tp + fn))
        ACCURACY: (tp + tn) / (tp + fp + fn + tn)
        PRECISION: tp / (tp + fp)
    """

    TPR = "TPR"
    FPR = "FPR"
    TNR = "TNR"
    FNR = "FNR"
    ACCURACY = "Accuracy"
    PRECISION = "Precision"
