"""Functools tools6 utilities"""

import functools


def lru_cache_2(maxsize=128):
    """LRU cache"""
    return functools.lru_cache(maxsize=maxsize)


def cached_property_2(func):
    """Cached property"""
    return functools.cached_property(func)
