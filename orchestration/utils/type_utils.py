"""Type utilities"""

from typing import Any, Type, get_origin, get_args


def get_type_name(t: Type) -> str:
    """Get type name"""
    return getattr(t, '__name__', str(t))


def is Optional(t: Type) -> bool:
    """Check if type is Optional"""
    return get_origin(t) is type(None)


def is_list(t: Type) -> bool:
    """Check if type is List"""
    return get_origin(t) is list


def is_dict(t: Type) -> bool:
    """Check if type is Dict"""
    return get_origin(t) is dict


def get_list_type(t: Type) -> Type:
    """Get List element type"""
    args = get_args(t)
    return args[0] if args else Any


def get_dict_types(t: Type) -> tuple:
    """Get Dict key/value types"""
    return get_args(t)
