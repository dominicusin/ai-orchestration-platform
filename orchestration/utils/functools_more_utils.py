"""More functools utilities"""

import functools
from typing import Callable, Any


def lru_cache_maxsize(maxsize: int = 128):
    """LRU cache decorator"""
    return functools.lru_cache(maxsize=maxsize)


def reduce_func(func: Callable, sequence: list, initial: Any = None):
    """Reduce function"""
    return functools.reduce(func, sequence, initial) if initial else functools.reduce(func, sequence)


def partial_func(func: Callable, *args, **kwargs) -> Callable:
    """Partial function"""
    return functools.partial(func, *args, **kwargs)


def singledispatch_func(func: Callable):
    """Single dispatch"""
    return functools.singledispatch(func)


def wraps_func(func: Callable) -> Callable:
    """Wraps decorator"""
    return functools.wraps(func)


def total_ordering(cls: type):
    """Total ordering decorator"""
    return functools.total_ordering(cls)


def cached_property(func: Callable) -> property:
    """Cached property"""
    return functools.cached_property(func)
