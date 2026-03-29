"""Itertools tools12 utilities"""

import itertools


def combinations_with_replacement_2(items: list, r: int):
    """Combinations with replacement"""
    return itertools.combinations_with_replacement(items, r)


def permutations_3(items: list, r: int = None):
    """Permutations"""
    return itertools.permutations(items, r)
