"""Itertools tools13 utilities"""

import itertools


def pairwise_2(iterable):
    """Pairwise"""
    return itertools.pairwise(iterable)


def batched_2(iterable, n):
    """Batched"""
    return itertools.batched(iterable, n)
