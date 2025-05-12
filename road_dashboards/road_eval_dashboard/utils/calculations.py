import numpy as np


def divide_consider_zero(a, b):
    """
    if denominator is zero, result is 0
    """
    return np.divide(a, b, out=np.zeros_like(a), where=b != 0)
