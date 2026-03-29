"""Itertools tools25 utilities"""

import itertools


def zip_2(*iterables):
    """Zip iterables"""
    return itertools.zip_longest(*iterables[:2]) if len(iterables) == 2 else zip(*iterables, strict=False)


def any_2(iterable):
    """Any"""
    return any(iterable)


def all_2(iterable):
    """All"""
    return all(iterable)
