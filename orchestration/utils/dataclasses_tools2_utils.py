"""Dataclasses tools2 utilities"""

import dataclasses


def dataclass_3(cls):
    """Dataclass"""
    return dataclasses.dataclass(cls)


def field_2(default=None):
    """Field"""
    return dataclasses.field(default=default)
