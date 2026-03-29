"""Collections tools utilities"""

import collections


def counter_items(counter: collections.Counter) -> list:
    """Get counter items"""
    return list(counter.items())


def counter_values(counter: collections.Counter) -> list:
    """Get counter values"""
    return list(counter.values())


def counter_keys(counter: collections.Counter) -> list:
    """Get counter keys"""
    return list(counter.keys())


def deque_items(deque: collections.deque) -> list:
    """Get deque items"""
    return list(deque)
