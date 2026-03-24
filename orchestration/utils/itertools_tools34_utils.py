"""Itertools tools34 utilities"""

import itertools


def islice_5(iterable, *args):
    """Islice"""
    return itertools.islice(iterable, *args)


def take_3(iterable, n):
    """Take"""
    return itertools.islice(iterable, n)
