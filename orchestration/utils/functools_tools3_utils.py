"""Functools tools3 utilities"""

import functools
from collections.abc import Callable


def cached_property_func(func: Callable) -> property:
    """Cached property"""
    return functools.cached_property(func)


def singledispatch_func(func: Callable) -> Callable:
    """Single dispatch"""
    return functools.singledispatch(func)


def total_ordering_cls(cls: type):
    """Total ordering class"""
    return functools.total_ordering(cls)
