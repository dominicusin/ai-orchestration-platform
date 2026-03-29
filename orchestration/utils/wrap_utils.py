"""Function wrapping utilities"""

import functools
from collections.abc import Callable


def wraps(wrapped: Callable, **kwargs):
    """ functools.wraps wrapper"""
    return functools.wraps(wrapped, **kwargs)


def update_wrapper(wrapper: Callable, wrapped: Callable, **kwargs):
    """Update wrapper"""
    return functools.update_wrapper(wrapper, wrapped, **kwargs)


def wraps_ex(func: Callable) -> Callable:
    """Extended wraps with more metadata"""
    def decorator(wrapper: Callable) -> Callable:
        w = functools.wraps(func)(wrapper)
        w.__wrapped__ = func
        return w
    return decorator


def accept_kwargs(func: Callable) -> Callable:
    """Accept any kwargs"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def accept_args(func: Callable) -> Callable:
    """Accept any args"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
