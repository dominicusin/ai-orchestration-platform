"""Functools utilities"""

import functools
from collections.abc import Callable
from typing import Any


def tap(value: Any, func: Callable = None) -> Any:
    """Tap into value for side effects"""
    if func:
        func(value)
    return value


def juxt(*funcs: Callable) -> Callable:
    """Juxtapose - apply all functions to value"""
    def applied(x):
        return [f(x) for f in funcs]
    return applied


def apply(func: Callable) -> Callable:
    """Apply function to value"""
    return lambda x: func(*x) if isinstance(x, tuple) else func(x)


def flip(func: Callable) -> Callable:
    """Flip function arguments"""
    @functools.wraps(func)
    def flipped(*args):
        return func(*reversed(args))
    return flipped


def complement(func: Callable) -> Callable:
    """Return complement of boolean function"""
    return lambda *args, **kwargs: not func(*args, **kwargs)
