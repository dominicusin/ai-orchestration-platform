"""Itertools tools20 utilities"""

import itertools


def product_3(*iterables, repeat=1):
    """Product"""
    return itertools.product(*iterables, repeat=repeat)


def tee_3(iterable, n=2):
    """Tee"""
    return itertools.tee(iterable, n)
