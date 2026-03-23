"""Enum utilities"""

import enum
from typing import List, Any


def enum_values(e: enum.Enum) -> List[Any]:
    """Get all enum values"""
    return [member.value for member in e]


def enum_names(e: enum.Enum) -> List[str]:
    """Get all enum names"""
    return [member.name for member in e]


def enum_members(e: enum.Enum) -> List[enum.Enum]:
    """Get all enum members"""
    return list(e)


def get_enum_by_value(e: enum.Enum, value: Any) -> enum.Enum:
    """Get enum member by value"""
    return e(value)


def get_enum_by_name(e: enum.Enum, name: str) -> enum.Enum:
    """Get enum member by name"""
    return getattr(e, name)
