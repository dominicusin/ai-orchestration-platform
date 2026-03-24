"""Datetime tools2 utilities"""

import datetime


def timedelta_2(days=0, seconds=0):
    """Timedelta"""
    return datetime.timedelta(days=days, seconds=seconds)


def date_fromisoformat(s):
    """Date from ISO format"""
    return datetime.date.fromisoformat(s)
