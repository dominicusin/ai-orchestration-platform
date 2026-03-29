"""Heapq tools utilities"""

import heapq
from typing import Any


def heappush_val(heap: list, val: Any):
    """Push value to heap"""
    heapq.heappush(heap, val)


def heappop_val(heap: list) -> Any:
    """Pop value from heap"""
    return heapq.heappop(heap)


def heapreplace_val(heap: list, val: Any) -> Any:
    """Replace heap top"""
    return heapq.heapreplace(heap, val)


def heapify_val(heap: list):
    """Heapify list"""
    heapq.heapify(heap)
