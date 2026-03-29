"""Weakref utilities"""

import functools
import weakref
from collections.abc import Callable
from typing import Any


def make_weakref(obj: Any):
    """Create weak reference"""
    return weakref.ref(obj)


def get_weakref(obj: Any):
    """Get weak reference"""
    return weakref.ref(obj)


def weak_callback(callback: Callable):
    """Create weak callback"""
    return weakref.finalize


class WeakMethod:
    """Weak method reference"""

    def __init__(self, method: Callable):
        self.ref = weakref.Method(method)

    def __call__(self):
        return self.ref()


def weak_cache(func: Callable) -> Callable:
    """Weak reference cache"""
    cache = weakref.WeakValueDictionary()

    @functools.wraps(func)
    def wrapper(*args):
        key = str(args)
        if key not in cache:
            cache[key] = func(*args)
        return cache[key]
    return wrapper
