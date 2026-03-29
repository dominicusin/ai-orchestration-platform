"""Itertools tools11 utilities"""

import itertools
from collections.abc import Iterator


def zip_longest_2(*iterables, fillvalue=None) -> Iterator:
    """Zip longest"""
    return itertools.zip_longest(*iterables, fillvalue=fillvalue)


def accumulate_2(iterable, func=None) -> Iterator:
    """Accumulate"""
    return itertools.accumulate(iterable, func) if func else itertools.accumulate(iterable)
