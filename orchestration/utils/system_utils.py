"""System utilities"""

import os
import platform
import sys


def get_system_info() -> dict:
    """Get system information"""
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
    }


def get_env(key: str, default: str = None) -> str:
    """Get environment variable"""
    return os.environ.get(key, default)


def set_env(key: str, value: str):
    """Set environment variable"""
    os.environ[key] = value


def is_debug() -> bool:
    """Check if running in debug mode"""
    return os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")


def get_cpu_count() -> int:
    """Get CPU count"""
    return os.cpu_count() or 1


def get_memory_info() -> dict:
    """Get memory info"""
    import psutil
    return {
        "total": psutil.virtual_memory().total,
        "available": psutil.virtual_memory().available,
        "percent": psutil.virtual_memory().percent,
    }
