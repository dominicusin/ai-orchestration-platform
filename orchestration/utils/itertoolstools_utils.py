"""Itertools tools utilities"""

import itertools
from typing import Iterator, List, Callable


def combinations_with_replacement(iterable: List, r: int) -> Iterator:
    """Combinations with replacement"""
    return itertools.combinations_with_replacement(iterable, r)


def permutations_with_r(iterable: List, r: int) -> Iterator:
    """Permutations with r"""
    return itertools.permutations(iterable, r)


def product_iter(*iterables, repeat: int = 1) -> Iterator:
    """Product of iterables"""
    return itertools.product(*iterables, repeat=repeat)


def zip_longest_fillvalue(fillvalue=None, *iterables):
    """Zip longest with fillvalue"""
    return itertools.zip_longest(*iterables, fillvalue=fillvalue)


def accumulate_custom(func: Callable, iterable: Iterator) -> Iterator:
    """Custom accumulate"""
    return itertools.accumulate(iterable, func)
