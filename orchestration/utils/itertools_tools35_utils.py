"""Itertools tools35 utilities"""

import itertools


def drop_3(iterable, n):
    """Drop"""
    return itertools.islice(iterable, n, None)


def filterfalse_4(func, iterable):
    """Filterfalse"""
    return itertools.filterfalse(func, iterable)
