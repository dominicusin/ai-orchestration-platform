"""Cache utilities"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any


class SimpleCache:
    """Simple in-memory cache"""

    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.store: dict[str, tuple] = {}

    def get(self, key: str) -> Any | None:
        if key in self.store:
            value, timestamp = self.store[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self.store[key]
        return None

    def set(self, key: str, value: Any):
        self.store[key] = (value, time.time())

    def delete(self, key: str):
        self.store.pop(key, None)

    def clear(self):
        self.store.clear()


def cached(ttl: int = 300):
    """Cache decorator"""
    cache = SimpleCache(ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            result = cache.get(key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(key, result)
            return result
        return wrapper
    return decorator
