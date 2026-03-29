"""Collections utilities"""

import collections
from collections import Counter


def counter(items: list) -> Counter:
    """Count items"""
    return collections.Counter(items)


def counter_most(counter: Counter, n: int = 10) -> list:
    """Get most common items"""
    return counter.most_common(n)


def deque_maxlen(maxlen: int = 100):
    """Create deque with maxlen"""
    return collections.deque(maxlen=maxlen)


def defaultdict_factory(default_type: type):
    """Create defaultdict with factory"""
    return collections.defaultdict(default_type)


def ordered_dict():
    """Create ordered dict"""
    return collections.OrderedDict()


def namedtuple_factory(name: str, fields: list[str]):
    """Create namedtuple"""
    return collections.namedtuple(name, fields)
