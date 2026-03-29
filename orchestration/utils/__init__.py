"""Utilities module"""

import hashlib
import json
from typing import Any


def hash_data(data: Any) -> str:
    """Hash data"""
    return hashlib.sha256(str(data).encode()).hexdigest()


def to_json(data: Any) -> str:
    """Convert to JSON"""
    return json.dumps(data, default=str)


def from_json(data: str) -> Any:
    """Parse JSON"""
    return json.loads(data)
