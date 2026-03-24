"""Itertools tools18 utilities"""

import itertools


def zip_longest_3(*iterables, fillvalue=None):
    """Zip longest"""
    return itertools.zip_longest(*iterables, fillvalue=fillvalue)


def filterfalse_3(predicate, iterable):
    """Filter false"""
    return itertools.filterfalse(predicate, iterable)
