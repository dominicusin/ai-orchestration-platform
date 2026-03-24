"""Functools tools2 utilities"""

import functools
from typing import Callable


def cache_clear_func(func: Callable):
    """Clear function cache"""
    if hasattr(func, 'cache_clear'):
        func.cache_clear()


def cache_info_func(func: Callable) -> dict:
    """Get cache info"""
    if hasattr(func, 'cache_info'):
        return func.cache_info()
    return {}


def partial_keyword(func: Callable, **kwargs) -> Callable:
    """Create partial with kwargs"""
    return functools.partial(func, **kwargs)
