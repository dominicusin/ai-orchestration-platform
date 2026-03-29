"""JSON utilities"""

import json
from typing import Any


def to_json(data: Any, pretty: bool = False) -> str:
    """Convert to JSON string"""
    indent = 2 if pretty else None
    return json.dumps(data, indent=indent, default=str)


def from_json(text: str) -> Any:
    """Parse JSON string"""
    return json.loads(text)


def to_file(data: Any, path: str, pretty: bool = False):
    """Write JSON to file"""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2 if pretty else None, default=str)


def from_file(path: str) -> Any:
    """Read JSON from file"""
    with open(path) as f:
        return json.load(f)


def merge(base: dict, update: dict) -> dict:
    """Deep merge JSON objects"""
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result
