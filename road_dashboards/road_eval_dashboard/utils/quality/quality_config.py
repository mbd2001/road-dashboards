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
