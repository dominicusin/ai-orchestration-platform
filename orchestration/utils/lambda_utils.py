"""Lambda utilities"""

from collections.abc import Callable
from typing import Any


def compose(*funcs: Callable) -> Callable:
    """Compose functions"""
    def composed(x):
        for f in funcs:
            x = f(x)
        return x
    return composed


def pipe(*funcs: Callable) -> Callable:
    """Pipe functions (left to right)"""
    return compose(*reversed(funcs))


def curry(func: Callable) -> Callable:
    """Curry function"""
    import functools
    return functools.partial(func)


def partial(func: Callable, **kwargs) -> Callable:
    """Partial application"""
    import functools
    return functools.partial(func, **kwargs)


def identity(x: Any) -> Any:
    """Identity function"""
    return x


def constant(x: Any) -> Callable:
    """Return constant function"""
    return lambda _: x
