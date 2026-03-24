"""Dataclasses utilities"""

import dataclasses
from typing import Any, Dict


def make_dataclass(name: str, fields: list):
    """Create dataclass dynamically"""
    return dataclasses.make_dataclass(name, fields)


def as_dict(obj) -> Dict:
    """Convert dataclass to dict"""
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return {}


def replace(obj, **kwargs):
    """Replace dataclass fields"""
    if dataclasses.is_dataclass(obj):
        return dataclasses.replace(obj, **kwargs)
    return obj


def fields_list(obj) -> list:
    """Get dataclass fields"""
    if dataclasses.is_dataclass(obj):
        return dataclasses.fields(obj)
    return []


def is_dataclass(obj) -> bool:
    """Check if dataclass"""
    return dataclasses.is_dataclass(obj)
