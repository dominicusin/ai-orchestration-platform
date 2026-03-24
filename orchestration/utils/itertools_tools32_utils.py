"""Itertools tools32 utilities"""

import itertools


def count_4(start=0, step=1):
    """Count"""
    return itertools.count(start, step)


def repeat_4(item, times=None):
    """Repeat"""
    return itertools.repeat(item, times)
