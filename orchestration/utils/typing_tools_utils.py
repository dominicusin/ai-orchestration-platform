"""Typing tools utilities"""

from typing import Any, TypeVar

T = TypeVar("T")


def optional_val(val: T | None) -> T | None:
    """Optional value"""
    return val


def list_type() -> list[Any]:
    """List type"""
    return list


def dict_type() -> dict[Any, Any]:
    """Dict type"""
    return dict
