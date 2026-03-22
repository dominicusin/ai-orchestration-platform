"""Decorator utilities"""

import functools
import time
from typing import Callable, Any


def once(func: Callable) -> Callable:
    """Execute only once"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not wrapper.called:
            wrapper.called = True
            return func(*args, **kwargs)
    wrapper.called = False
    return wrapper


def timing(func: Callable) -> Callable:
    """Time function execution"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        wrapper.elapsed = time.perf_counter() - start
        return result
    return wrapper


def memoize(func: Callable) -> Callable:
    """Memoize function results"""
    cache = {}
    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper


def deprecated(message: str = "This function is deprecated"):
    """Mark function as deprecated"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            warnings.warn(message, DeprecationWarning)
            return func(*args, **kwargs)
        return wrapper
    return decorator
