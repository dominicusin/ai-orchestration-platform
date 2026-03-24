"""Itertools tools3 utilities"""

import itertools
from typing import List, Iterator


def pairwise_iter(iterable: Iterator) -> Iterator:
    """Pairwise iterator"""
    return itertools.pairwise(iterable)


def batched_iter(iterable: Iterator, n: int) -> Iterator:
    """Batch iterator"""
    return itertools.batched(iterable, n)


def accumulate_iter(iterable: Iterator) -> Iterator:
    """Accumulate iterator"""
    return itertools.accumulate(iterable)
