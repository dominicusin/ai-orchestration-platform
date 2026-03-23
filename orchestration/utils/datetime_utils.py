"""Datetime utilities"""

from datetime import datetime, timedelta, timezone
from typing import Optional


def now_utc() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def now_local() -> datetime:
    """Get current local datetime"""
    return datetime.now()


def parse_iso(date_str: str) -> datetime:
    """Parse ISO date string"""
    return datetime.fromisoformat(date_str)


def to_timestamp(dt: datetime) -> float:
    """Convert datetime to timestamp"""
    return dt.timestamp()


def from_timestamp(ts: float) -> datetime:
    """Convert timestamp to datetime"""
    return datetime.fromtimestamp(ts)


def add_days(dt: datetime, days: int) -> datetime:
    """Add days to datetime"""
    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """Add hours to datetime"""
    return dt + timedelta(hours=hours)
