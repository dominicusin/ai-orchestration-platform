"""Collections more utilities"""

import collections
from typing import List, Any


def counter_update(counter: collections.Counter, items: List) -> collections.Counter:
    """Update counter with items"""
    counter.update(items)
    return counter


def counter_subtract(counter: collections.Counter, items: List) -> collections.Counter:
    """Subtract items from counter"""
    counter.subtract(items)
    return counter


def deque_appendleft(deque: collections.deque, item: Any):
    """Append to left of deque"""
    deque.appendleft(item)


def deque_maxlen(deque: collections.deque) -> int:
    """Get maxlen of deque"""
    return deque.maxlen or 0
