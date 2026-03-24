"""OS utilities"""

import os
import sys
from typing import List, Optional


def get_cwd() -> str:
    """Get current working directory"""
    return os.getcwd()


def chdir(path: str):
    """Change directory"""
    os.chdir(path)


def list_dir(path: str = ".") -> List[str]:
    """List directory"""
    return os.listdir(path)


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable"""
    return os.environ.get(key, default)


def set_env(key: str, value: str):
    """Set environment variable"""
    os.environ[key] = value


def get_pid() -> int:
    """Get process ID"""
    return os.getpid()


def is_file(path: str) -> bool:
    """Check if file"""
    return os.path.isfile(path)


def is_dir(path: str) -> bool:
    """Check if directory"""
    return os.path.isdir(path)
