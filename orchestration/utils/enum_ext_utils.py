"""Enum extended utilities"""

import enum
from typing import Any


def enum_to_list(e: enum.Enum) -> list[Any]:
    """Convert enum to list"""
    return [member.value for member in e]


def enum_to_dict(e: enum.Enum) -> dict:
    """Convert enum to dict"""
    return {member.name: member.value for member in e}


def enum_from_value(e: enum.Enum, value: Any) -> enum.Enum:
    """Get enum member from value"""
    return e(value)


def enum_from_name(e: enum.Enum, name: str) -> enum.Enum:
    """Get enum member from name"""
    return getattr(e, name)


def auto_enum():
    """Auto-numbered enum"""
    return enum.auto


def enum_iter(e: enum.Enum) -> list[enum.Enum]:
    """Iterate enum members"""
    return list(e)
