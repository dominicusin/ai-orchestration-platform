"""Functools tools13 utilities"""

import functools


def singledispatch_3(func):
    """Singledispatch"""
    return functools.singledispatch(func)


def total_ordering_3(cls):
    """Total ordering"""
    return functools.total_ordering(cls)
