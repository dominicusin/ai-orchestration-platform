"""Itertools tools40 utilities"""

import itertools


def islice_6(iterable, start, stop=None):
    """Islice from start"""
    return itertools.islice(iterable, start, stop)


def takewhile_4(predicate, iterable):
    """Takewhile"""
    return itertools.takewhile(predicate, iterable)
