"""Itertools tools43 utilities"""

import itertools


def combinations_with_replacement_3(iterable, r):
    """Combinations with replacement"""
    return itertools.combinations_with_replacement(iterable, r)


def chain_from_iterable_2(iterable):
    """Chain from iterable"""
    return itertools.chain.from_iterable(iterable)
