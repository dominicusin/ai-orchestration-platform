"""Operator utilities"""

import operator
from typing import Callable, Any


def attrgetter(attr: str) -> Callable:
    """Get attribute from object"""
    return operator.attrgetter(attr)


def itemgetter(item: Any) -> Callable:
    """Get item from object"""
    return operator.itemgetter(item)


def methodcaller(method: str, *args, **kwargs) -> Callable:
    """Call method on object"""
    return operator.methodcaller(method, *args, **kwargs)


def lt(a: Any, b: Any) -> bool:
    """Less than"""
    return operator.lt(a, b)


def gt(a: Any, b: Any) -> bool:
    """Greater than"""
    return operator.gt(a, b)


def eq(a: Any, b: Any) -> bool:
    """Equal"""
    return operator.eq(a, b)


def ne(a: Any, b: Any) -> bool:
    """Not equal"""
    return operator.ne(a, b)


def is_(a: Any, b: Any) -> bool:
    """Is same object"""
    return operator.is_(a, b)


def is_not(a: Any, b: Any) -> bool:
    """Is not same object"""
    return operator.is_not(a, b)
