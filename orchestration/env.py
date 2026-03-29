"""Environment utilities"""

import os
from typing import Any


def getenv(key: str, default: Any = None) -> Any:
    """Get environment variable"""
    return os.environ.get(key, default)


def setenv(key: str, value: str):
    """Set environment variable"""
    os.environ[key] = value


def get_bool(key: str, default: bool = False) -> bool:
    """Get boolean env var"""
    value = os.environ.get(key, "").lower()
    return value in ("true", "1", "yes") if value else default


def get_int(key: str, default: int = 0) -> int:
    """Get int env var"""
    try:
        return int(os.environ.get(key, default))
    except ValueError:
        return default


def get_list(key: str, separator: str = ",", default: list = None) -> list:
    """Get list env var"""
    value = os.environ.get(key)
    if not value:
        return default or []
    return [v.strip() for v in value.split(separator)]


def to_dict(prefix: str) -> dict[str, str]:
    """Get all env vars with prefix"""
    return {
        key[len(prefix):]: value
        for key, value in os.environ.items()
        if key.startswith(prefix)
    }
