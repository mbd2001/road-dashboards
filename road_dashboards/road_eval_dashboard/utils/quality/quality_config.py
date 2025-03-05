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


class MetricType(Enum):
    """
    Enum that defines the type of metric to be used in the query.

    Attributes:
        CORRECT_ACCEPTANCE_RATE: Correct Acceptance / (Correct Acceptance + Incorrect Acceptance)
        INCORRECT_ACCEPTANCE_RATE: Incorrect Acceptance / (Correct Acceptance + Incorrect Acceptance)
        INCORRECT_REJECTION_RATE: Incorrect Rejection / (Correct Rejection + Incorrect Rejection)
        CORRECT_REJECTION_RATE: Correct Rejection / (Correct Rejection + Incorrect Rejection)
        ACCURACY: (Correct Acceptance + Correct Rejection) / (Correct Acceptance + Correct Rejection + Incorrect Acceptance+Incorrect Rejection)
        PRECISION: Correct Acceptance / (Correct Acceptance + Incorrect Rejection)
    """

    CORRECT_ACCEPTANCE_RATE = "Correct Acceptance Rate"
    INCORRECT_ACCEPTANCE_RATE = "Incorrect Acceptance Rate"
    INCORRECT_REJECTION_RATE = "Incorrect Rejection Rate"
    CORRECT_REJECTION_RATE = "Correct Rejection Rate"
    ACCURACY = "Accuracy"
    PRECISION = "Precision"


QUALITY_METRIC_TEMPLATE = (
    "CAST(COUNT(CASE WHEN {num_condition} THEN 1 ELSE NULL END) AS DOUBLE) / "
    'COUNT(CASE WHEN {denom_condition} THEN 1 ELSE NULL END) AS "score_{ind}"'
)
