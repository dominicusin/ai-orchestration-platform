"""Copy tools utilities"""

import copy


def copy_2(obj):
    """Shallow copy"""
    return copy.copy(obj)


def deepcopy_2(obj):
    """Deep copy"""
    return copy.deepcopy(obj)
