"""Collections tools5 utilities"""

import collections


def chainmap_2(*maps):
    """ChainMap"""
    return collections.ChainMap(*maps)


def namedtuple_2(name, fields):
    """Namedtuple"""
    return collections.namedtuple(name, fields)
