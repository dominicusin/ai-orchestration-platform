"""Inspection utilities"""

import inspect
from collections.abc import Callable


def get_signature(func: Callable) -> dict:
    """Get function signature"""
    sig = inspect.signature(func)
    return {
        "name": func.__name__,
        "params": [p.name for p in sig.parameters.values()],
        "defaults": {p.name: p.default for p in sig.parameters.values() if p.default != inspect.Parameter.empty}
    }


def get_source(func: Callable) -> str:
    """Get function source code"""
    return inspect.getsource(func)


def get_callable_name(func: Callable) -> str:
    """Get callable name"""
    return func.__name__


def get_args(func: Callable, args: tuple, kwargs: dict) -> dict:
    """Get function arguments as dict"""
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


def is_async(func: Callable) -> bool:
    """Check if function is async"""
    return inspect.iscoroutinefunction(func)


def get_properties(obj: object) -> list[str]:
    """Get object properties"""
    return [p for p in dir(obj) if not p.startswith('_')]
