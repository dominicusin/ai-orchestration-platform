"""Itertools more utilities"""

import itertools
from collections.abc import Iterator


def combinations_r(items: list, r: int) -> Iterator:
    """Combinations with replacement"""
    return itertools.combinations_with_replacement(items, r)


def permutations_count(items: list, r: int) -> int:
    """Count permutations"""
    return len(list(itertools.permutations(items, r)))


def product_repeat(items: list, repeat: int) -> Iterator:
    """Product with repeat"""
    return itertools.product(items, repeat=repeat)


def islice_start_stop(iterable: Iterator, start: int, stop: int) -> Iterator:
    """Slice iterator with start and stop"""
    return itertools.islice(iterable, start, stop)
