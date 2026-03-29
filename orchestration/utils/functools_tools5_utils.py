"""Functools tools5 utilities"""

import functools
from collections.abc import Callable


def partialmethod(func: Callable, *args, **kwargs):
    """Partial method"""
    return functools.partialmethod(func, *args, **kwargs)


def cache_on_disk_func(func: Callable):
    """Cache on disk (stub)"""
    return func
