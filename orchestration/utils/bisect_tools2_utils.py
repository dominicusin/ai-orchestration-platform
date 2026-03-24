"""Bisect tools2 utilities"""

import bisect


def insort_left_2(a, x):
    """Insort left"""
    bisect.insort_left(a, x)


def insort_right_2(a, x):
    """Insort right"""
    bisect.insort_right(a, x)
