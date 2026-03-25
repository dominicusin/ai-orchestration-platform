"""Bisect tools3 utilities"""

import bisect


def bisect_left_3(a, x):
    """Bisect left"""
    return bisect.bisect_left(a, x)


def bisect_right_3(a, x):
    """Bisect right"""
    return bisect.bisect_right(a, x)
