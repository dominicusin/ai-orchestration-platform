"""Itertools tools10 utilities"""

import itertools
from typing import Iterator


def compress_2(iterable, selectors) -> Iterator:
    """Compress"""
    return itertools.compress(iterable, selectors)


def groupby_2(iterable, key=None) -> Iterator:
    """Groupby"""
    return itertools.groupby(iterable, key)
