"""Functools tools8 utilities"""

import functools


def wraps_2(func):
    """Wraps decorator"""
    def decorator(f):
        return functools.update_wrapper(f, func)
    return decorator


def singledispatch_2(func):
    """Singledispatch"""
    return functools.singledispatch(func)
