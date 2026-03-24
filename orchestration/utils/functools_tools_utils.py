"""Functools tools utilities"""

import functools
from typing import Callable


@functools.lru_cache(maxsize=128)
def cached_func(func: Callable) -> Callable:
    """Cached function"""
    return func


def reduce_func(func: Callable, iterable: list, initial: any = None):
    """Reduce function"""
    return functools.reduce(func, iterable, initial) if initial else functools.reduce(func, iterable)


def partial_func(func: Callable, *args, **kwargs) -> Callable:
    """Partial function"""
    return functools.partial(func, *args, **kwargs)
