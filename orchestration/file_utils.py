"""File utilities for DAG execution"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("orchestration.file_utils")


def ensure_dir(path: str):
    """Ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)


def list_files(path: str, pattern: str = "*") -> List[str]:
    """List files in directory"""
    return [str(p) for p in Path(path).glob(pattern) if p.is_file()]


def read_file(path: str) -> str:
    """Read file content"""
    return Path(path).read_text()


def write_file(path: str, content: str):
    """Write file content"""
    ensure_dir(str(Path(path).parent))
    Path(path).write_text(content)


def copy_file(src: str, dst: str):
    """Copy file"""
    ensure_dir(str(Path(dst).parent))
    shutil.copy2(src, dst)


def delete_file(path: str):
    """Delete file"""
    if Path(path).exists():
        Path(path).unlink()


def get_size(path: str) -> int:
    """Get file size"""
    return Path(path).stat().st_size


def get_extension(path: str) -> str:
    """Get file extension"""
    return Path(path).suffix