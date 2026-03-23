"""Functools extensions"""

import functools
from typing import Callable


def cache_unlimited(func: Callable) -> Callable:
    """Unlimited cache (same as lru_cache(None))"""
    return functools.lru_cache(maxsize=None)(func)


def cached_func(func: Callable) -> Callable:
    """Cached function with maxsize 128"""
    return functools.lru_cache(maxsize=128)(func)


def reduce_with_initial(func: Callable, sequence: list, initial):
    """Reduce with initial value"""
    return functools.reduce(func, sequence, initial)


def singledispatch_impl(func: Callable):
    """Single dispatch implementation"""
    return functools.singledispatch(func)


def wraps_with_updated(func: Callable) -> Callable:
    """Wraps with updated docs"""
    def wrapper(wrapped: Callable) -> Callable:
        return functools.wraps(wrapped, updated=[])(wrapped)
    return wrapper
