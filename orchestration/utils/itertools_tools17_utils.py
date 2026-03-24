"""Itertools tools17 utilities"""

import itertools


def groupby_3(iterable, key=None):
    """Groupby with key"""
    return itertools.groupby(iterable, key)


def compress_3(data, selectors):
    """Compress data"""
    return itertools.compress(data, selectors)
