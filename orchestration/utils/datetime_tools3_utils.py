"""Datetime tools3 utilities"""

import datetime


def datetime_fromisoformat(s):
    """Datetime from ISO format"""
    return datetime.datetime.fromisoformat(s)


def time_now():
    """Time now"""
    return datetime.time.now()
