"""Type utilities"""

from typing import Any, get_args, get_origin


def get_type_name(t: type) -> str:
    """Get type name"""
    return getattr(t, '__name__', str(t))


def is_optional(t: type) -> bool:
    """Check if type is Optional"""
    return get_origin(t) is type(None)


def is_list(t: type) -> bool:
    """Check if type is List"""
    return get_origin(t) is list


def is_dict(t: type) -> bool:
    """Check if type is Dict"""
    return get_origin(t) is dict


def get_list_type(t: type) -> type:
    """Get List element type"""
    args = get_args(t)
    return args[0] if args else Any


def get_dict_types(t: type) -> tuple:
    """Get Dict key/value types"""
    return get_args(t)
