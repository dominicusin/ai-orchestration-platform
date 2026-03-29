"""Datetime utilities"""

import datetime


def now_utc():
    """Now UTC"""
    return datetime.datetime.now(datetime.UTC)


def today_date():
    """Today date"""
    return datetime.date.today()
