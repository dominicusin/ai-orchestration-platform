"""Bisect tools4 utilities"""

import bisect


def insort_left_3(a, x):
    """Insort left"""
    bisect.insort_left(a, x)


def insort_right_3(a, x):
    """Insort right"""
    bisect.insort_right(a, x)
