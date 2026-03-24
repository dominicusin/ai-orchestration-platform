"""Collections tools2 utilities"""

import collections
from typing import Any


def ordered_dict_get(ordered_dict: collections.OrderedDict, key: Any, default: Any = None) -> Any:
    """Get from ordered dict"""
    return ordered_dict.get(key, default)


def ordered_dict_items(ordered_dict: collections.OrderedDict):
    """Get ordered dict items"""
    return ordered_dict.items()


def namedtuple_create(name: str, fields: list):
    """Create namedtuple"""
    return collections.namedtuple(name, fields)
