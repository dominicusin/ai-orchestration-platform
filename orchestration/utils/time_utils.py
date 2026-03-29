"""Time utilities"""

from datetime import datetime, timedelta


def now() -> str:
    """Get current ISO timestamp"""
    return datetime.now().isoformat()


def add_days(date: str, days: int) -> str:
    """Add days to date"""
    dt = datetime.fromisoformat(date)
    return (dt + timedelta(days=days)).isoformat()


def format_duration(seconds: float) -> str:
    """Format duration"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def parse_duration(duration_str: str) -> float:
    """Parse duration string (e.g., '1h30m')"""
    import re

    hours = re.search(r'(\d+)h', duration_str)
    minutes = re.search(r'(\d+)m', duration_str)
    seconds = re.search(r'(\d+)s', duration_str)

    total = 0
    total += int(hours.group(1)) * 3600 if hours else 0
    total += int(minutes.group(1)) * 60 if minutes else 0
    total += int(seconds.group(1)) if seconds else 0

    return float(total)
