"""Functools tools utilities"""

import functools
from collections.abc import Callable


def cache_on_disk(func: Callable) -> Callable:
    """Cache function results on disk"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def method_cache(method: Callable) -> Callable:
    """Cache method results"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        return method(self, *args, **kwargs)
    return wrapper


def class_property(func: Callable) -> property:
    """Class property decorator"""
    return classmethod(property(func))


def decorator_with_args(func: Callable = None, *, arg1=None, arg2=None):
    """Decorator with arguments"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator if func is None else decorator(func)
