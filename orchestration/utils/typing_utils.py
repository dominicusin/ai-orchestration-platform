"""Typing utilities"""

from typing import Any, Union, get_args, get_origin, get_type_hints


def get_type_hints_func(func) -> dict:
    """Get type hints"""
    return get_type_hints(func)


def get_origin_type(t) -> Any:
    """Get origin type"""
    return get_origin(t)


def get_args_type(t) -> tuple:
    """Get type args"""
    return get_args(t)


def is_union_type(t) -> bool:
    """Check if union type"""
    return get_origin(t) is Union


def is_optional_type(t) -> bool:
    """Check if optional type"""
    return is_union_type(t) and type(None) in get_args(t)


def is_list_type(t) -> bool:
    """Check if list type"""
    return get_origin(t) is list


def is_dict_type(t) -> bool:
    """Check if dict type"""
    return get_origin(t) is dict
