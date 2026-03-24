"""Inspect extended utilities"""

import inspect
from typing import Callable, Any, List


def get_func_signature(func: Callable) -> inspect.Signature:
    """Get function signature"""
    return inspect.signature(func)


def get_func_params(func: Callable) -> List[str]:
    """Get function parameters"""
    return list(inspect.signature(func).parameters.keys())


def is_async_func(func: Callable) -> bool:
    """Check if async function"""
    return inspect.iscoroutinefunction(func)


def is_generator_func(func: Callable) -> bool:
    """Check if generator function"""
    return inspect.isgeneratorfunction(func)


def get_func_source(func: Callable) -> str:
    """Get function source code"""
    try:
        return inspect.getsource(func)
    except:
        return ""


def get_func_name(func: Callable) -> str:
    """Get function name"""
    return func.__name__
