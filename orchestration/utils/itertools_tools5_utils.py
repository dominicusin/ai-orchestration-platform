"""Itertools tools5 utilities"""

import itertools
from collections.abc import Callable, Iterator


def groupby_key(iterable: Iterator, key: Callable | None = None) -> Iterator:
    """Group by key"""
    return itertools.groupby(iterable, key)


def tee_n(iterable: Iterator, n: int = 2) -> list[Iterator]:
    """Tee iterable"""
    return itertools.tee(iterable, n)


def zip_longest_fill(iterable1: Iterator, iterable2: Iterator, fillvalue=None) -> Iterator:
    """Zip longest with fill"""
    return itertools.zip_longest(iterable1, iterable2, fillvalue=fillvalue)
