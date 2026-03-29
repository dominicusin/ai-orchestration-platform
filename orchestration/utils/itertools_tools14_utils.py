"""Itertools tools14 utilities"""

import itertools


def islice_3(iterable, stop):
    """Islice"""
    return itertools.islice(iterable, stop)


def take_2(iterable, n):
    """Take n items"""
    return itertools.islice(iterable, n)
