"""Sys utilities"""

import sys
import os
from typing import List


def get_version() -> str:
    """Get Python version"""
    return sys.version


def get_platform() -> str:
    """Get platform"""
    return sys.platform


def get_executable() -> str:
    """Get executable path"""
    return sys.executable


def get_args() -> List[str]:
    """Get command line args"""
    return sys.argv


def get_env_paths() -> List[str]:
    """Get PATH environment variable"""
    return os.environ.get('PATH', '').split(os.pathsep)


def get_modules() -> dict:
    """Get loaded modules"""
    return sys.modules


def exit(code: int = 0):
    """Exit with code"""
    sys.exit(code)
