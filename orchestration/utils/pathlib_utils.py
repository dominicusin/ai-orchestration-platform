"""Pathlib utilities"""

from pathlib import Path
from typing import List, Optional


def path_exists(path: str) -> bool:
    """Check if path exists"""
    return Path(path).exists()


def path_is_file(path: str) -> bool:
    """Check if path is file"""
    return Path(path).is_file()


def path_is_dir(path: str) -> bool:
    """Check if path is directory"""
    return Path(path).is_dir()


def path_read_text(path: str, encoding: str = "utf-8") -> str:
    """Read text from path"""
    return Path(path).read_text(encoding=encoding)


def path_write_text(path: str, content: str, encoding: str = "utf-8"):
    """Write text to path"""
    Path(path).write_text(content, encoding=encoding)


def path_glob(pattern: str, root: str = ".") -> List[Path]:
    """Glob pattern"""
    return list(Path(root).glob(pattern))


def path_rglob(pattern: str, root: str = ".") -> List[Path]:
    """Recursive glob"""
    return list(Path(root).rglob(pattern))
