"""Itertools tools19 utilities"""

import itertools


def accumulate_3(iterable, func=None):
    """Accumulate"""
    return itertools.accumulate(iterable) if func is None else itertools.accumulate(iterable, func)


def combinations_3(iterable, r):
    """Combinations"""
    return itertools.combinations(iterable, r)
