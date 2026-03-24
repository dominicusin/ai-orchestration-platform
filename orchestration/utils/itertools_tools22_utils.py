"""Itertools tools22 utilities"""

import itertools


def takewhile_3(func, iterable):
    """Takewhile"""
    return itertools.takewhile(func, iterable)


def starmap_2(func, iterable):
    """Starmap"""
    return itertools.starmap(func, iterable)
