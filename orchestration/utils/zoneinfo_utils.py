"""Zoneinfo utilities"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def get_timezone(tz_name: str) -> ZoneInfo:
    """Get timezone by name"""
    return ZoneInfo(tz_name)


def now_in_timezone(tz_name: str) -> datetime:
    """Get current time in timezone"""
    return datetime.now(ZoneInfo(tz_name))


def convert_to_timezone(dt: datetime, tz_name: str) -> datetime:
    """Convert datetime to timezone"""
    return dt.astimezone(ZoneInfo(tz_name))


def is_dst(dt: datetime) -> bool:
    """Check if datetime is in DST"""
    return bool(dt.dst())


def utc_now() -> datetime:
    """Get current UTC time"""
    return datetime.now(UTC)
