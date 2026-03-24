"""Copy extended utilities"""

import copy
from typing import Any


def shallow_copy_obj(obj: Any) -> Any:
    """Shallow copy object"""
    return copy.copy(obj)


def deep_copy_obj(obj: Any) -> Any:
    """Deep copy object"""
    return copy.deepcopy(obj)


def copy_with_callback(obj: Any, callback: callable = None) -> Any:
    """Copy with callback"""
    result = copy.deepcopy(obj)
    if callback:
        callback(result)
    return result


def deepcopy_recursive(obj: Any, memo: dict = None) -> Any:
    """Recursive deep copy with memo"""
    return copy.deepcopy(obj, memo=memo or {})
