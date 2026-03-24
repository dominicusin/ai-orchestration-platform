"""Dataclasses tools utilities"""

import dataclasses


def dataclass_2(cls):
    """Dataclass"""
    return dataclasses.dataclass(cls)


def field_default(default=None):
    """Field with default"""
    return dataclasses.field(default=default)
