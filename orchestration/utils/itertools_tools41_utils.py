"""Itertools tools41 utilities"""

import itertools


def dropwhile_4(predicate, iterable):
    """Dropwhile"""
    return itertools.dropwhile(predicate, iterable)


def starmap_3(func, iterable):
    """Starmap"""
    return itertools.starmap(func, iterable)
