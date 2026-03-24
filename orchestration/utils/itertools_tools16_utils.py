"""Itertools tools16 utilities"""

import itertools


def count_3(start=0, step=1):
    """Count from start"""
    return itertools.count(start, step)


def chain_from_iterable(iterable):
    """Chain from iterable"""
    return itertools.chain.from_iterable(iterable)
