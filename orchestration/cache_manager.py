"""Cache utilities"""

import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("orchestration.cache_manager")


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class CacheManager:
    """In-memory cache with TTL"""

    def __init__(self):
        self.cache: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        if key in self.cache:
            entry = self.cache[key]
            if entry.expires_at > time.time():
                return entry.value
            del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 300):
        self.cache[key] = CacheEntry(
            value=value,
            expires_at=time.time() + ttl,
        )

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        self.cache.clear()


_cache: CacheManager | None = None


def get_cache() -> CacheManager:
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache
