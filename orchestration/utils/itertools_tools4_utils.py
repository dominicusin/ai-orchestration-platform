"""Itertools tools4 utilities"""

import itertools
from collections.abc import Callable, Iterator


def compress_data(iterable: list, selectors: list) -> Iterator:
    """Compress data"""
    return itertools.compress(iterable, selectors)


def dropwhile_pred(predicate: Callable, iterable: Iterator) -> Iterator:
    """Drop while predicate"""
    return itertools.dropwhile(predicate, iterable)


def takewhile_pred(predicate: Callable, iterable: Iterator) -> Iterator:
    """Take while predicate"""
    return itertools.takewhile(predicate, iterable)
