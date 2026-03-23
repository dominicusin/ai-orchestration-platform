"""Copy utilities"""

import copy
from typing import Any, Dict


def shallow_copy(obj: Any) -> Any:
    """Shallow copy"""
    return copy.copy(obj)


def deep_copy(obj: Any) -> Any:
    """Deep copy"""
    return copy.deepcopy(obj)


def copy_dict(obj: Dict) -> Dict:
    """Copy dictionary"""
    return obj.copy()


def deepcopy_dict(obj: Dict) -> Dict:
    """Deep copy dictionary"""
    return copy.deepcopy(obj)


def copy_obj(obj: Any, deep: bool = False) -> Any:
    """Copy any object"""
    return deep_copy(obj) if deep else shallow_copy(obj)
