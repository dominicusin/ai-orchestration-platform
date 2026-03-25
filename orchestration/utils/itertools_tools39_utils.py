"""Itertools tools39 utilities"""

import itertools


def groupby_4(iterable, key=None):
    """Groupby"""
    return itertools.groupby(iterable, key)


def compress_4(iterable, selectors):
    """Compress"""
    return itertools.compress(iterable, selectors)
