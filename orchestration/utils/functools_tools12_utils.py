"""Functools tools12 utilities"""

import functools


def lru_cache_3(maxsize=128):
    """LRU cache"""
    return functools.lru_cache(maxsize=maxsize)


def cached_property_3(func):
    """Cached property"""
    return functools.cached_property(func)
