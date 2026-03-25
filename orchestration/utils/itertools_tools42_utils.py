"""Itertools tools42 utilities"""

import itertools


def pairwise_3(iterable):
    """Pairwise"""
    return itertools.pairwise(iterable)


def batched_3(iterable, n):
    """Batched"""
    return itertools.batched(iterable, n)
