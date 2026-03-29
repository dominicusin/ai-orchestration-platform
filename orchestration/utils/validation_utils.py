"""Validation utilities"""

import re


def is_email(value: str) -> bool:
    """Validate email"""
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value))


def is_url(value: str) -> bool:
    """Validate URL"""
    return bool(re.match(r'^https?://[\w\.-]+\.\w+', value))


def is_ip(value: str) -> bool:
    """Validate IP address"""
    parts = value.split('.')
    if len(parts) != 4:
        return False
    return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def is_json(value: str) -> bool:
    """Validate JSON"""
    import json
    try:
        json.loads(value)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def validate_range(value: int, min_val: int, max_val: int) -> bool:
    """Validate value in range"""
    return min_val <= value <= max_val


def validate_length(value: str, min_len: int = 0, max_len: int = 1000) -> bool:
    """Validate string length"""
    return min_len <= len(value) <= max_len
