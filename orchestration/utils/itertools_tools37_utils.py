"""Itertools tools37 utilities"""

import itertools


def permutations_4(iterable, r=None):
    """Permutations"""
    return itertools.permutations(iterable, r)


def product_4(*iterables, repeat=1):
    """Product"""
    return itertools.product(*iterables, repeat=repeat)
