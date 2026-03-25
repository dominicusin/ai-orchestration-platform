"""Collections tools7 utilities"""

import collections


def defaultdict_3(default_factory):
    """Defaultdict"""
    return collections.defaultdict(default_factory)


def ordereddict_3():
    """OrderedDict"""
    return collections.OrderedDict()
