"""Calendar utilities"""

import calendar


def get_month_days(year: int, month: int) -> int:
    """Get number of days in month"""
    return calendar.monthrange(year, month)[1]


def is_leap_year(year: int) -> bool:
    """Check if leap year"""
    return calendar.isleap(year)


def get_calendar(year: int, month: int) -> list:
    """Get calendar for month"""
    return calendar.monthcalendar(year, month)


def month_name(month: int) -> str:
    """Get month name"""
    return calendar.month_name(month)


def day_name(day: int) -> str:
    """Get day name"""
    return calendar.day_name[day]
