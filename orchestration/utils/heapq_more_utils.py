"""Heapq more utilities"""

import heapq
from typing import List, Any


def heap_push_item(heap: List, item: Any, key: callable = None):
    """Push item with key function"""
    if key:
        item = (key(item), item)
    heapq.heappush(heap, item)


def heap_pop_item(heap: List, key: callable = None) -> Any:
    """Pop item with key function"""
    item = heapq.heappop(heap)
    if key and isinstance(item, tuple):
        return item[1]
    return item


def heap_replace_item(heap: List, item: Any) -> Any:
    """Replace item and return old"""
    return heapq.heapreplace(heap, item)


def heapify_custom(items: List, key: callable = None):
    """Heapify with key function"""
    if key:
        items = [(key(item), item) for item in items]
    heapq.heapify(items)
    return items
