"""Itertools tools7 utilities"""

import itertools
from typing import Iterator


def count_2(start: int = 0, step: int = 1) -> Iterator:
    """Count from start"""
    return itertools.count(start, step)


def cycle_2(iterable: Iterator) -> Iterator:
    """Cycle iterable"""
    return itertools.cycle(iterable)


def repeat_2(obj, times: int = None) -> Iterator:
    """Repeat object"""
    return itertools.repeat(obj, times)
