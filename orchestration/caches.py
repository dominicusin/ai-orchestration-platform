"""Pipeline caches"""

import logging
from collections import OrderedDict
from typing import Any

logger = logging.getLogger("orchestration.caches")


class Cache:
    """Base cache"""

    def get(self, key: str) -> Any | None:
        raise NotImplementedError

    def set(self, key: str, value: Any):
        raise NotImplementedError

    def delete(self, key: str):
        raise NotImplementedError


class LRUCache(Cache):
    """LRU cache"""

    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.cache: OrderedDict = {}

    def get(self, key: str) -> Any | None:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]


