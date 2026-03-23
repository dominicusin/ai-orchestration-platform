"""Itertools extensions"""

import itertools
from typing import List, Iterator, Callable


def takewhile_pred(predicate: Callable, iterable: Iterator) -> Iterator:
    """Take while predicate is true"""
    return itertools.takewhile(predicate, iterable)


def dropwhile_pred(predicate: Callable, iterable: Iterator) -> Iterator:
    """Drop while predicate is true"""
    return itertools.dropwhile(predicate, iterable)


def groupby_key(iterable: Iterator, key: Callable = None) -> Iterator:
    """Group by key"""
    return itertools.groupby(iterable, key)


def compress_data(selectors: List, iterable: List) -> Iterator:
    """Compress iterable by selectors"""
    return itertools.compress(iterable, selectors)


def islice_advanced(iterable: Iterator, *args) -> Iterator:
    """Advanced islice"""
    return itertools.islice(iterable, *args)


def tee_iterable(iterable: Iterator, n: int = 2) -> List[Iterator]:
    """Tee iterable"""
    return itertools.tee(iterable, n)
