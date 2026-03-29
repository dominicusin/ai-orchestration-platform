"""Itertools tools28 utilities"""



def min_2(iterable, key=None, default=None):
    """Min"""
    return min(iterable, key=key, default=default) if default else min(iterable, key=key)


def max_2(iterable, key=None, default=None):
    """Max"""
    return max(iterable, key=key, default=default) if default else max(iterable, key=key)
