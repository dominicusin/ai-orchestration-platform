"""Statistics utilities"""

import statistics


def mean_val(values: list[float]) -> float:
    """Calculate mean"""
    return statistics.mean(values)


def median_val(values: list[float]) -> float:
    """Calculate median"""
    return statistics.median(values)


def mode_val(values: list) -> any:
    """Calculate mode"""
    return statistics.mode(values)


def stdev_val(values: list[float]) -> float:
    """Calculate standard deviation"""
    return statistics.stdev(values)


def variance_val(values: list[float]) -> float:
    """Calculate variance"""
    return statistics.variance(values)
