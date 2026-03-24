"""Itertools tools36 utilities"""

import itertools


def accumulate_4(iterable, func=None):
    """Accumulate"""
    return itertools.accumulate(iterable, func) if func else itertools.accumulate(iterable)


def combinations_4(iterable, r):
    """Combinations"""
    return itertools.combinations(iterable, r)
