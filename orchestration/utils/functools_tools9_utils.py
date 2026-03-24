"""Functools tools9 utilities"""

import functools


def total_ordering_2(cls):
    """Total ordering"""
    return functools.total_ordering(cls)


def cmp_to_key_2(func):
    """Cmp to key"""
    return functools.cmp_to_key(func)
