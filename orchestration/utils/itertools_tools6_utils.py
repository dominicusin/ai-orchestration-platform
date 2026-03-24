"""Itertools tools6 utilities"""

import itertools
from typing import List


def combinations_2(items: List, r: int) -> itertools.combinations:
    """Combinations"""
    return itertools.combinations(items, r)


def permutations_2(items: List, r: int = None) -> itertools.permutations:
    """Permutations"""
    return itertools.permutations(items, r)


def product_2(*items) -> itertools.product:
    """Product"""
    return itertools.product(*items)
