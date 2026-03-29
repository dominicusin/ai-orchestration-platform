"""JSON utilities extended"""

import json
from typing import Any


def to_json_pretty(data: Any) -> str:
    """Convert to pretty JSON"""
    return json.dumps(data, indent=2, sort_keys=True)


def from_json_strict(text: str) -> Any:
    """Parse JSON strictly"""
    return json.loads(text, strict=True)


def json_encoder_default(obj: Any) -> Any:
    """Default JSON encoder"""
    return json.JSONEncoder().default(obj)


def json_decoder_object(pairs: list) -> dict:
    """Custom JSON object decoder"""
    return dict(pairs)


def safe_json_parse(text: str, default: Any = None) -> Any:
    """Safe JSON parse"""
    try:
        return json.loads(text)
    except Exception:
        return default
