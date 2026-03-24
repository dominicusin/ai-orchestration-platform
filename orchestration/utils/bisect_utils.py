"""Bisect utilities"""

import bisect
from typing import List, Any


def bisect_left_pos(items: List, x: Any) -> int:
    """Find left insertion position"""
    return bisect.bisect_left(items, x)


def bisect_right_pos(items: List, x: Any) -> int:
    """Find right insertion position"""
    return bisect.bisect_right(items, x)


def insort_left_pos(items: List, x: Any):
    """Insert at left position"""
    bisect.insort_left(items, x)


def insort_right_pos(items: List, x: Any):
    """Insert at right position"""
    bisect.insort_right(items, x)