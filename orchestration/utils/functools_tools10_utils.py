"""Functools tools10 utilities"""

import functools


def update_wrapper_2(wrapper, wrapped):
    """Update wrapper"""
    return functools.update_wrapper(wrapper, wrapped)


def wraps_3(wrapped):
    """Wraps decorator"""
    return functools.wraps(wrapped)
