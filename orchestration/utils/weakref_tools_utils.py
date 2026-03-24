"""Weakref tools utilities"""

import weakref


def weakref_ref(obj):
    """Weak reference"""
    return weakref.ref(obj)


def weakref_cache(obj):
    """Weak value dictionary"""
    return weakref.WeakValueDictionary()
