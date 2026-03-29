"""Collection utilities"""

from typing import Any


def group_by(items: list[dict], key: str) -> dict[Any, list[dict]]:
    """Group items by key"""
    result = {}
    for item in items:
        k = item.get(key)
        if k not in result:
            result[k] = []
        result[k].append(item)
    return result


def unique(items: list) -> list:
    """Get unique items preserving order"""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def sort_by(items: list[dict], key: str, reverse: bool = False) -> list[dict]:
    """Sort items by key"""
    return sorted(items, key=lambda x: x.get(key), reverse=reverse)


def filter_by(items: list[dict], **kwargs) -> list[dict]:
    """Filter items by key-value pairs"""
    result = []
    for item in items:
        if all(item.get(k) == v for k, v in kwargs.items()):
            result.append(item)
    return result


def find(items: list[dict], **kwargs) -> dict:
    """Find first matching item"""
    for item in items:
        if all(item.get(k) == v for k, v in kwargs.items()):
            return item
    return None
