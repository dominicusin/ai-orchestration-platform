"""Itertools tools21 utilities"""

import itertools


def islice_4(iterable, *args):
    """Islice"""
    return itertools.islice(iterable, *args)


def dropwhile_3(func, iterable):
    """Dropwhile"""
    return itertools.dropwhile(func, iterable)
