"""Enum tools utilities"""

import enum


def enum_auto():
    """Auto enum"""
    return enum.auto()


def enum_enum(cls):
    """Enum class"""
    return enum.Enum(cls)
