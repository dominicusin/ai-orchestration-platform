"""Datetime tools5 utilities"""

import datetime


def timedelta_3(days=0, seconds=0):
    """Timedelta"""
    return datetime.timedelta(days=days, seconds=seconds)


def time_2():
    """Time now"""
    return datetime.time.now()
