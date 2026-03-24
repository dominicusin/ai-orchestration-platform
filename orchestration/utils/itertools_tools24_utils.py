"""Itertools tools24 utilities"""

import itertools


def chain_3(*iterables):
    """Chain iterables"""
    return itertools.chain(*iterables)


def enumerate_2(iterable, start=0):
    """Enumerate"""
    return itertools.enumerate(iterable, start)
