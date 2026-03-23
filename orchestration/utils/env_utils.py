"""Environment utilities"""

import os
from typing import Any, Optional


def get_env(key: str, default: Any = None, required: bool = False) -> Any:
    """Get environment variable"""
    value = os.environ.get(key, default)
    if required and value is None:
        raise ValueError(f"Required env var {key} is not set")
    return value


def get_int(key: str, default: int = 0) -> int:
    """Get environment variable as int"""
    return int(os.environ.get(key, default))


def get_bool(key: str, default: bool = False) -> bool:
    """Get environment variable as bool"""
    value = os.environ.get(key, str(default)).lower()
    return value in ("1", "true", "yes", "on")


def get_list(key: str, separator: str = ",", default: list = None) -> list:
    """Get environment variable as list"""
    value = os.environ.get(key)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(separator)]


def set_env(key: str, value: Any):
    """Set environment variable"""
    os.environ[key] = str(value)


def load_env(path: str = ".env"):
    """Load .env file"""
    from pathlib import Path
    env_path = Path(path)
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()
