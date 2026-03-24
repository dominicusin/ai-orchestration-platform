"""Math utilities"""

import math
from typing import List


def clamp_val(value: float, min_val: float, max_val: float) -> float:
    """Clamp value"""
    return max(min_val, min(max_val, value))


def lerp_val(a: float, b: float, t: float) -> float:
    """Linear interpolation"""
    return a + (b - a) * t


def map_val(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """Map value range"""
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def avg_val(values: List[float]) -> float:
    """Average value"""
    return sum(values) / len(values) if values else 0


def sum_val(values: List[float]) -> float:
    """Sum values"""
    return sum(values)