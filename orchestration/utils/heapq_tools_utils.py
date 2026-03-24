"""Heapq tools utilities"""

import heapq
from typing import List, Any


def heappush_val(heap: List, val: Any):
    """Push value to heap"""
    heapq.heappush(heap, val)


def heappop_val(heap: List) -> Any:
    """Pop value from heap"""
    return heapq.heappop(heap)


def heapreplace_val(heap: List, val: Any) -> Any:
    """Replace heap top"""
    return heapq.heapreplace(heap, val)


def heapify_val(heap: List):
    """Heapify list"""
    heapq.heapify(heap)
