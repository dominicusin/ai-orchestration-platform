"""Itertools tools12 utilities"""

import itertools
from typing import List


def combinations_with_replacement_2(items: List, r: int):
    """Combinations with replacement"""
    return itertools.combinations_with_replacement(items, r)


def permutations_3(items: List, r: int = None):
    """Permutations"""
    return itertools.permutations(items, r)
