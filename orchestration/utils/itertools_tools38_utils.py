"""Itertools tools38 utilities"""

import itertools


def tee_4(iterable, n=2):
    """Tee"""
    return itertools.tee(iterable, n)


def zip_longest_4(*iterables, fillvalue=None):
    """Zip longest"""
    return itertools.zip_longest(*iterables, fillvalue=fillvalue)
