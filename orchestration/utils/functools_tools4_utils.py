"""Functools tools4 utilities"""

import functools
from collections.abc import Callable


def wraps_update(wrapper: Callable, wrapped: Callable):
    """Update wrapper"""
    return functools.update_wrapper(wrapper, wrapped)


def reduce_right(func: Callable, iterable: list):
    """Reduce from right"""
    return functools.reduce(func, reversed(iterable))


def cmp_to_key(func: Callable):
    """Convert cmp to key"""
    return functools.cmp_to_key(func)
