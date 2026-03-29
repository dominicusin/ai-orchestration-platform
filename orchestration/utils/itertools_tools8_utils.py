"""Itertools tools8 utilities"""

import itertools
from collections.abc import Iterator


def chain_2(*iterables) -> Iterator:
    """Chain iterables"""
    return itertools.chain(*iterables)


def islice_2(iterable: Iterator, *args) -> Iterator:
    """Slice iterator"""
    return itertools.islice(iterable, *args)


def tee_2(iterable: Iterator, n: int = 2) -> list[Iterator]:
    """Tee iterable"""
    return itertools.tee(iterable, n)
