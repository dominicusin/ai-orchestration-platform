"""Functools more utilities"""

import functools
from collections.abc import Callable


def lru_cache_typed(maxsize: int = 128):
    """LRU cache with type hints"""
    return functools.lru_cache(maxsize=maxsize)


def cache_clear(func: Callable):
    """Clear cache"""
    func.cache_clear()


def cache_info(func: Callable):
    """Get cache info"""
    return func.cache_info()


def singledispatch_register(func: Callable, type: type):
    """Register for singledispatch"""
    return func.register(type)
