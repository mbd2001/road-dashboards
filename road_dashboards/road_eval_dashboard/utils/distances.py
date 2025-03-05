from enum import Enum

import numpy as np

SECONDS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]


class PolynomialEvalDistances(Enum):
    """Constants for polynomial evaluation distances."""

    SECS_AHEAD = [1.3, 3.0]
    ALLOWED_ERROR_AT_SECS_AHEAD = [0.2, 0.5]


def compute_distances_dict(
    secs_ahead: list[float] = PolynomialEvalDistances.SECS_AHEAD.value,
    allowed_error_at_secs_ahead: list[float] = PolynomialEvalDistances.ALLOWED_ERROR_AT_SECS_AHEAD.value,
):
    """
    Compute the distances dict for the given secs_ahead and allowed_error_at_secs_ahead.
    The distances are computed using a 1d polynomial.
    """
    coeff = np.polyfit(secs_ahead, allowed_error_at_secs_ahead, deg=1)
    threshold_polynomial = np.poly1d(coeff)
    distances_dict = {sec: max(threshold_polynomial(sec), 0.2) for sec in SECONDS}
    return distances_dict


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
