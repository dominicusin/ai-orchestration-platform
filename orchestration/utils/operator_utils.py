"""Operator utilities"""

import operator
from typing import Any


def attr_getter(name: str):
    """Get attribute"""
    return operator.attrgetter(name)


def item_getter(index: Any):
    """Get item"""
    return operator.itemgetter(index)


def method_caller(name: str, *args):
    """Call method"""
    return operator.methodcaller(name, *args)


def lt_op(a: Any, b: Any) -> bool:
    """Less than"""
    return operator.lt(a, b)


def gt_op(a: Any, b: Any) -> bool:
    """Greater than"""
    return operator.gt(a, b)


def eq_op(a: Any, b: Any) -> bool:
    """Equal"""
    return operator.eq(a, b)
