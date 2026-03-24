"""Itertools tools33 utilities"""

import itertools


def cycle_4(iterable):
    """Cycle"""
    return itertools.cycle(iterable)


def chain_4(*iterables):
    """Chain"""
    return itertools.chain(*iterables)
