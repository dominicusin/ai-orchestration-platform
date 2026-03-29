"""Enum utilities"""

import enum
from typing import Any, TypeVar

E = TypeVar("E", bound=enum.Enum)


def enum_values(e: type[enum.Enum]) -> list[Any]:
    """Get all enum values"""
    return [member.value for member in e]


def enum_names(e: type[enum.Enum]) -> list[str]:
    """Get all enum names"""
    return [member.name for member in e]


def enum_members(e: type[enum.Enum]) -> list[enum.Enum]:
    """Get all enum members"""
    return list(e.__members__.values())


def get_enum_by_value(e: type[enum.Enum], value: Any) -> enum.Enum:
    """Get enum member by value"""
    return e(value)


def get_enum_by_name(e: type[enum.Enum], name: str) -> enum.Enum:
    """Get enum member by name"""
    return getattr(e, name)
