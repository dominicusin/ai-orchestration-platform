"""Path utilities"""

from pathlib import Path
from typing import List


def resolve_path(path: str) -> Path:
    """Resolve path"""
    return Path(path).resolve()


def get_relative(path: str, base: str) -> Path:
    """Get relative path"""
    return Path(path).relative_to(base)


def join_paths(*parts: str) -> Path:
    """Join path parts"""
    return Path(*parts)


def list_dirs(path: str) -> List[str]:
    """List directories"""
    return [str(p) for p in Path(path).iterdir() if p.is_dir()]


def list_files(path: str, pattern: str = "*") -> List[str]:
    """List files matching pattern"""
    return [str(p) for p in Path(path).glob(pattern)]
