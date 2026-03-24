"""Functools tools7 utilities"""

import functools


def reduce_2(func, iterable, initial=None):
    """Reduce"""
    return functools.reduce(func, iterable, initial) if initial else functools.reduce(func, iterable)


def partial_2(func, *args, **kwargs):
    """Partial"""
    return functools.partial(func, *args, **kwargs)
