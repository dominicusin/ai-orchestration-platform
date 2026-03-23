"""Bisect utilities"""

import bisect
from typing import List, Any


def bisect_left(items: List, x: Any) -> int:
    """Find left insertion point"""
    return bisect.bisect_left(items, x)


def bisect_right(items: List, x: Any) -> int:
    """Find right insertion point"""
    return bisect.bisect_right(items, x)


def insort_left(items: List, x: Any):
    """Insert item in sorted order (left)"""
    bisect.insort_left(items, x)


def insort_right(items: List, x: Any):
    """Insert item in sorted order (right)"""
    bisect.insort_right(items, x)


def bisect_find(items: List, x: Any) -> bool:
    """Check if item exists in sorted list"""
    idx = bisect.bisect_left(items, x)
    return idx < len(items) and items[idx] == x
