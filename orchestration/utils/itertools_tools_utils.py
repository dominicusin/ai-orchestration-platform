"""Itertools tools utilities"""

import itertools
from collections.abc import Iterator


def count_start(step: int = 1) -> Iterator:
    """Count from 0 by step"""
    return itertools.count(step=step)


def cycle_list(items: list) -> Iterator:
    """Cycle list"""
    return itertools.cycle(items)


def repeat_val(val: any, times: int = None) -> Iterator:
    """Repeat value"""
    return itertools.repeat(val, times)


def chain_lists(*lists) -> Iterator:
    """Chain lists"""
    return itertools.chain(*lists)
