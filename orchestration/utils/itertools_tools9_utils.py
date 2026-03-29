"""Itertools tools9 utilities"""

import itertools
from collections.abc import Iterator


def filterfalse_2(predicate, iterable: Iterator) -> Iterator:
    """Filter false"""
    return itertools.filterfalse(predicate, iterable)


def takewhile_2(predicate, iterable: Iterator) -> Iterator:
    """Take while"""
    return itertools.takewhile(predicate, iterable)


def dropwhile_2(predicate, iterable: Iterator) -> Iterator:
    """Drop while"""
    return itertools.dropwhile(predicate, iterable)
