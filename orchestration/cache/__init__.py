"""Cache module"""

import time
from typing import Any, Optional

from .cache import CachePolicy, CacheStats, FileCache
from .redis_cache import (
    RedisCache,
    RedisCacheConfig,
    create_redis_cache,
    get_redis_cache,
)


class Cache:
    """Simple cache"""

    def __init__(self):
        self.store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self.store.get(key)

    def set(self, key: str, value: Any):
        self.store[key] = value

    def delete(self, key: str):
        self.store.pop(key, None)

    def clear(self):
        self.store.clear()


def get_cache() -> Cache:
    return Cache()


__all__ = [
    "Cache",
    "CachePolicy",
    "CacheStats",
    "FileCache",
    "RedisCache",
    "RedisCacheConfig",
    "get_redis_cache",
    "create_redis_cache",
]
