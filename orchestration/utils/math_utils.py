"""Math utilities"""

import math
from typing import List


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation"""
    return a + (b - a) * t


def map_range(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """Map value from one range to another"""
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def average(numbers: List[float]) -> float:
    """Calculate average"""
    return sum(numbers) / len(numbers) if numbers else 0


def median(numbers: List[float]) -> float:
    """Calculate median"""
    sorted_nums = sorted(numbers)
    n = len(sorted_nums)
    if n % 2 == 0:
        return (sorted_nums[n//2-1] + sorted_nums[n//2]) / 2
    return sorted_nums[n//2]


def std_dev(numbers: List[float]) -> float:
    """Calculate standard deviation"""
    if not numbers:
        return 0
    avg = average(numbers)
    variance = sum((x - avg) ** 2 for x in numbers) / len(numbers)
    return math.sqrt(variance)
