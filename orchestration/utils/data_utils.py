"""Data utilities"""

from typing import Any


def flatten(data: Any) -> list:
    """Flatten nested structure"""
    if isinstance(data, list):
        result = []
        for item in data:
            result.extend(flatten(item))
        return result
    return [data]


def chunk(items: list, size: int) -> list[list]:
    """Split list into chunks"""
    return [items[i:i+size] for i in range(0, len(items), size)]


def deep_merge(dict1: dict, dict2: dict) -> dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def to_snake_case(text: str) -> str:
    """Convert to snake_case"""
    import re
    text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', text).lower()


def to_camel_case(text: str) -> str:
    """Convert to camelCase"""
    components = text.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])
