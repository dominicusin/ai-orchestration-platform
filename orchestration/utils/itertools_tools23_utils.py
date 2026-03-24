"""Itertools tools23 utilities"""

import itertools


def map_2(func, *iterables):
    """Map"""
    return itertools.map(func, *iterables)


def filter_2(func, iterable):
    """Filter"""
    return itertools.filterfalse(lambda x: not func(x), iterable) if func else iterable
