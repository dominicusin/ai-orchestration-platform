"""Utility functions"""

import os
import sys
import hashlib
import logging
from typing import Any, Dict, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("orchestration.utils_helpers")


def get_version() -> str:
    """Get version"""
    return "4.0.0"


def ensure_directory(path: str):
    """Ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_timestamp() -> str:
    """Get current timestamp"""
    return datetime.now().isoformat()


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Hash string"""
    if algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text.encode()).hexdigest()
    return hashlib.sha256(text.encode()).hexdigest()


def truncate(text: str, length: int = 100, suffix: str = "...") -> str:
    """Truncate text"""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def parse_size(size_str: str) -> int:
    """Parse size string (e.g., '10MB')"""
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
    
    for unit, multiplier in units.items():
        if size_str.upper().endswith(unit):
            value = float(size_str[:-len(unit)])
            return int(value * multiplier)
    
    return int(size_str)


def format_size(size_bytes: int) -> str:
    """Format size"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes}{unit}"
        size_bytes /= 1024
    return f"{size_bytes}TB"


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def chunk_list(items: List, size: int) -> List[List]:
    """Split list into chunks"""
    return [items[i:i + size] for i in range(0, len(items), size)]


def clamp(value: int, min_val: int, max_val: int) -> int:
    """Clamp value"""
    return max(min_val, min(max_val, value))
