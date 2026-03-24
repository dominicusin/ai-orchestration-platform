"""Itertools tools15 utilities"""

import itertools


def repeat_3(item, times=None):
    """Repeat item"""
    return itertools.repeat(item, times)


def cycle_3(iterable):
    """Cycle iterable"""
    return itertools.cycle(iterable)
