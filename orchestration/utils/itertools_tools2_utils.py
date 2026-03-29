"""Itertools tools2 utilities"""

import itertools
from collections.abc import Iterator


def islice_iter(iterable: Iterator, stop: int) -> Iterator:
    """Slice iterator"""
    return itertools.islice(iterable, stop)


def take_n(iterable: Iterator, n: int) -> list:
    """Take n items"""
    return list(itertools.islice(iterable, n))


def drop_n(iterable: Iterator, n: int) -> Iterator:
    """Drop n items"""
    for i, item in enumerate(iterable):
        if i >= n:
            yield item


def filter_none(iterable: Iterator) -> Iterator:
    """Filter None values"""
    return itertools.filterfalse(lambda x: x is None, iterable)
