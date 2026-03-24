"""Statistics utilities"""

import statistics
from typing import List


def mean_val(values: List[float]) -> float:
    """Calculate mean"""
    return statistics.mean(values)


def median_val(values: List[float]) -> float:
    """Calculate median"""
    return statistics.median(values)


def mode_val(values: List) -> any:
    """Calculate mode"""
    return statistics.mode(values)


def stdev_val(values: List[float]) -> float:
    """Calculate standard deviation"""
    return statistics.stdev(values)


def variance_val(values: List[float]) -> float:
    """Calculate variance"""
    return statistics.variance(values)