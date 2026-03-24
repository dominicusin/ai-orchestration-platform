"""Collections tools utilities"""

import collections
from typing import List


def counter_items(counter: collections.Counter) -> List:
    """Get counter items"""
    return list(counter.items())


def counter_values(counter: collections.Counter) -> List:
    """Get counter values"""
    return list(counter.values())


def counter_keys(counter: collections.Counter) -> List:
    """Get counter keys"""
    return list(counter.keys())


def deque_items(deque: collections.deque) -> List:
    """Get deque items"""
    return list(deque)
