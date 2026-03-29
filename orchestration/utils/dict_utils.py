"""Dictionary utilities"""

from typing import Any


def deep_get(d: dict, key: str, default: Any = None) -> Any:
    """Deep get nested dict value"""
    keys = key.split('.')
    result = d
    for k in keys:
        if isinstance(result, dict):
            result = result.get(k)
        else:
            return default
        if result is None:
            return default
    return result


def deep_set(d: dict, key: str, value: Any):
    """Deep set nested dict value"""
    keys = key.split('.')
    current = d
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    current[keys[-1]] = value


def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """Flatten nested dict"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def filter_dict(d: dict, keys: list[str]) -> dict:
    """Filter dict by keys"""
    return {k: v for k, v in d.items() if k in keys}
