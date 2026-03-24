"""Functools tools11 utilities"""

import functools


def partial_3(func, *args, **kwargs):
    """Partial"""
    return functools.partial(func, *args, **kwargs)


def reduce_3(func, iterable, initial=None):
    """Reduce"""
    return functools.reduce(func, iterable, initial) if initial else functools.reduce(func, iterable)
