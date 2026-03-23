"""Statistics utilities"""

import statistics
from typing import List


def mean(values: List[float]) -> float:
    """Calculate mean"""
    return statistics.mean(values)


def median(values: List[float]) -> float:
    """Calculate median"""
    return statistics.median(values)


def mode(values: List) -> any:
    """Calculate mode"""
    return statistics.mode(values)


def stdev(values: List[float]) -> float:
    """Calculate standard deviation"""
    return statistics.stdev(values)


def variance(values: List[float]) -> float:
    """Calculate variance"""
    return statistics.variance(values)


def quantiles(values: List[float], n: int = 4) -> List[float]:
    """Calculate quantiles"""
    return statistics.quantiles(values, n=n)
