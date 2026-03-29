"""More itertools utilities"""

import itertools
from collections.abc import Callable, Iterator
from typing import Any


def count_func(start: int = 0, step: int = 1) -> Iterator[int]:
    """Count from start by step"""
    return itertools.count(start, step)


def cycle_iter(items: list) -> Iterator:
    """Cycle through items infinitely"""
    return itertools.cycle(items)


def repeat_item(item: Any, times: int = None) -> Iterator:
    """Repeat item"""
    return itertools.repeat(item, times)


def chain_iter(*iterables) -> Iterator:
    """Chain iterables"""
    return itertools.chain(*iterables)


def islice_iter(iterator: Iterator, stop: int, start: int = 0, step: int = 1) -> Iterator:
    """Slice iterator"""
    return itertools.islice(iterator, start, stop, step)


def filterfalse_func(func: Callable, iterable: Iterator) -> Iterator:
    """Filter false"""
    return itertools.filterfalse(func, iterable)


def accumulate_iter(iterable: Iterator, func: Callable = None) -> Iterator:
    """Accumulate"""
    return itertools.accumulate(iterable, func) if func else itertools.accumulate(iterable)
