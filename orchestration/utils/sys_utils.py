"""Sys utilities"""

import os
import sys


def get_version() -> str:
    """Get Python version"""
    return sys.version


def get_platform() -> str:
    """Get platform"""
    return sys.platform


def get_executable() -> str:
    """Get executable path"""
    return sys.executable


def get_args() -> list[str]:
    """Get command line args"""
    return sys.argv


def get_env_paths() -> list[str]:
    """Get PATH environment variable"""
    return os.environ.get('PATH', '').split(os.pathsep)


def get_modules() -> dict:
    """Get loaded modules"""
    return sys.modules


def exit(code: int = 0):
    """Exit with code"""
    sys.exit(code)
