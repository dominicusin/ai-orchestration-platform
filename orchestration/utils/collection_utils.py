"""Collection utilities"""

from typing import List, Dict, Any, Callable


def group_by(items: List[Dict], key: str) -> Dict[Any, List[Dict]]:
    """Group items by key"""
    result = {}
    for item in items:
        k = item.get(key)
        if k not in result:
            result[k] = []
        result[k].append(item)
    return result


def unique(items: List) -> List:
    """Get unique items preserving order"""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def sort_by(items: List[Dict], key: str, reverse: bool = False) -> List[Dict]:
    """Sort items by key"""
    return sorted(items, key=lambda x: x.get(key), reverse=reverse)


def filter_by(items: List[Dict], **kwargs) -> List[Dict]:
    """Filter items by key-value pairs"""
    result = []
    for item in items:
        if all(item.get(k) == v for k, v in kwargs.items()):
            result.append(item)
    return result


def find(items: List[Dict], **kwargs) -> Dict:
    """Find first matching item"""
    for item in items:
        if all(item.get(k) == v for k, v in kwargs.items()):
            return item
    return None
