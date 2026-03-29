"""Collections tools3 utilities"""

import collections


def defaultdict_2(default_type):
    """Defaultdict with default factory"""
    return collections.defaultdict(default_type)


def ordereddict_2():
    """OrderedDict"""
    return collections.OrderedDict()
