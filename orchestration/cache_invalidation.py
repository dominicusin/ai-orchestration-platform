"""
Cache invalidation strategies
Стратегии инвалидации кэша
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheEntry:
    """Запись кэша"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    expires_at: float = None
    tags: set = field(default_factory=set)
    hit_count: int = 0


class CacheInvalidator:
    """Инвалидатор кэша"""

    def __init__(self):
        self._entries: dict[str, CacheEntry] = {}
        self._listeners: list[Callable] = []

    def register_listener(self, callback: Callable):
        """Регистрация слушателя"""
        self._listeners.append(callback)

    def _notify(self, key: str, reason: str):
        """Уведомление слушателей"""
        for listener in self._listeners:
            try:
                listener(key, reason)
            except Exception:
                pass

    def invalidate(self, key: str, reason: str = "manual"):
        """Инвалидация по ключу"""
        if key in self._entries:
            del self._entries[key]
            self._notify(key, reason)

    def invalidate_pattern(self, pattern: str, reason: str = "pattern"):
        """Инвалидация по паттерну"""
        import re
        regex = re.compile(pattern)
        keys_to_delete = [k for k in self._entries.keys() if regex.match(k)]

        for key in keys_to_delete:
            self.invalidate(key, reason)

    def invalidate_tag(self, tag: str, reason: str = "tag"):
        """Инвалидация по тегу"""
        keys_to_delete = [
            key for key, entry in self._entries.items()
            if tag in entry.tags
        ]

        for key in keys_to_delete:
            self.invalidate(key, reason)

    def invalidate_older_than(self, seconds: float, reason: str = "ttl"):
        """Инвалидация старых записей"""
        cutoff = time.time() - seconds
        keys_to_delete = [
            key for key, entry in self._entries.items()
            if entry.created_at < cutoff
        ]

        for key in keys_to_delete:
            self.invalidate(key, reason)

    def invalidate_expired(self, reason: str = "expired"):
        """Инвалидация истёкших"""
        now = time.time()
        keys_to_delete = [
            key for key, entry in self._entries.items()
            if entry.expires_at and entry.expires_at < now
        ]

        for key in keys_to_delete:
            self.invalidate(key, reason)

    def invalidate_least_used(self, count: int, reason: str = "lru"):
        """Инвалидация наименее используемых"""
        if count >= len(self._entries):
            return

        sorted_entries = sorted(
            self._entries.items(),
            key=lambda x: x[1].hit_count
        )

        for key, _ in sorted_entries[:count]:
            self.invalidate(key, reason)

    def clear_all(self, reason: str = "clear"):
        """Очистка всего кэша"""
        keys = list(self._entries.keys())
        for key in keys:
            self.invalidate(key, reason)

    def get_stats(self) -> dict:
        """Получение статистики"""
        total_hits = sum(e.hit_count for e in self._entries.values())
        return {
            "total_entries": len(self._entries),
            "total_hits": total_hits,
            "avg_hits": total_hits / len(self._entries) if self._entries else 0,
        }


class TTLCache:
    """Кэш с TTL"""

    def __init__(self, default_ttl: float = 3600):
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._invalidator = CacheInvalidator()

    def get(self, key: str) -> Any | None:
        """Получение значения"""
        entry = self._cache.get(key)
        if entry is None:
            return None

        # Check expiration
        if entry.expires_at and entry.expires_at < time.time():
            self._invalidator.invalidate(key, "expired")
            return None

        entry.hit_count += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: float = None, tags: list = None):
        """Установка значения"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None

        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            expires_at=expires_at,
            tags=set(tags) if tags else set(),
        )

    def delete(self, key: str):
        """Удаление"""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Очистка"""
        self._cache.clear()
        self._invalidator.clear_all("clear")

    def invalidate_pattern(self, pattern: str):
        """Инвалидация по паттерну"""
        import re
        regex = re.compile(pattern)
        keys_to_delete = [k for k in self._cache.keys() if regex.match(k)]
        for key in keys_to_delete:
            if key in self._cache:
                del self._cache[key]

    def invalidate_tag(self, tag: str):
        """Инвалидация по тегу"""
        keys_to_delete = [
            key for key, entry in self._cache.items()
            if tag in entry.tags
        ]
        for key in keys_to_delete:
            if key in self._cache:
                del self._cache[key]

    def get_stats(self) -> dict:
        """Статистика"""
        return {
            **self._invalidator.get_stats(),
            "cache_size": len(self._cache),
        }


# Singleton
_cache: TTLCache | None = None


def get_ttl_cache(ttl: float = 3600) -> TTLCache:
    """Получение TTL кэша"""
    global _cache
    if _cache is None:
        _cache = TTLCache(ttl)
    return _cache
