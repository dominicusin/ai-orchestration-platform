"""Heap utilities"""

import heapq
from typing import Any


def heap_push(heap: list, item: Any):
    """Push item to heap"""
    heapq.heappush(heap, item)


def heap_pop(heap: list) -> Any:
    """Pop item from heap"""
    return heapq.heappop(heap)


def heap_replace(heap: list, item: Any) -> Any:
    """Replace item and return old"""
    return heapq.heapreplace(heap, item)


def nlargest(n: int, items: list) -> list:
    """Get n largest items"""
    return heapq.nlargest(n, items)


def nsmallest(n: int, items: list) -> list:
    """Get n smallest items"""
    return heapq.nsmallest(n, items)


def merge(*iterables: list) -> list:
    """Merge sorted iterables"""
    return list(heapq.merge(*iterables))
