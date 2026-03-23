"""Heap utilities"""

import heapq
from typing import List, Any


def heap_push(heap: List, item: Any):
    """Push item to heap"""
    heapq.heappush(heap, item)


def heap_pop(heap: List) -> Any:
    """Pop item from heap"""
    return heapq.heappop(heap)


def heap_replace(heap: List, item: Any) -> Any:
    """Replace item and return old"""
    return heapq.heapreplace(heap, item)


def nlargest(n: int, items: List) -> List:
    """Get n largest items"""
    return heapq.nlargest(n, items)


def nsmallest(n: int, items: List) -> List:
    """Get n smallest items"""
    return heapq.nsmallest(n, items)


def merge(*iterables: List) -> List:
    """Merge sorted iterables"""
    return list(heapq.merge(*iterables))
