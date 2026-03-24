"""Inspect tools utilities"""

import inspect


def getsource_2(func):
    """Get source"""
    return inspect.getsource(func)


def getsignature_2(func):
    """Get signature"""
    return inspect.signature(func)
