"""Itertools tools8 utilities"""

import itertools
from typing import Iterator, List


def chain_2(*iterables) -> Iterator:
    """Chain iterables"""
    return itertools.chain(*iterables)


def islice_2(iterable: Iterator, *args) -> Iterator:
    """Slice iterator"""
    return itertools.islice(iterable, *args)


def tee_2(iterable: Iterator, n: int = 2) -> List[Iterator]:
    """Tee iterable"""
    return itertools.tee(iterable, n)
