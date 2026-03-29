"""Redis cache integration"""

import logging
import os
from typing import Any

logger = logging.getLogger("orchestration.redis_cache")

# Try to import redis, fallback to stub
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisCache:
    """Redis cache wrapper with real implementation"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str | None = None,
        decode_responses: bool = True,
    ):
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db
        self.password = password or os.getenv("REDIS_PASSWORD")
        self._decode_responses = decode_responses
        self._client: Any = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("redis package not installed, using stub")
            self._connected = False
            return False

        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=self._decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self._client.ping()
            self._connected = True
            logger.info(f"Redis connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self._connected = False
            return False

    @property
    def connected(self) -> bool:
        return self._connected

    def get(self, key: str) -> str | None:
        """Get value by key"""
        if not self._connected or self._client is None:
            return None
        try:
            return self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set key-value with TTL"""
        if not self._connected or self._client is None:
            return False
        try:
            self._client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key"""
        if not self._connected or self._client is None:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DEL error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._connected or self._client is None:
            return False
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    def get_many(self, keys: list[str]) -> dict[str, str | None]:
        """Get multiple keys"""
        if not self._connected or self._client is None:
            return dict.fromkeys(keys)
        try:
            return self._client.mget(keys) or {}
        except Exception as e:
            logger.error(f"Redis MGET error: {e}")
            return dict.fromkeys(keys)

    def set_many(self, mapping: dict[str, str], ttl: int = 300) -> bool:
        """Set multiple keys"""
        if not self._connected or self._client is None:
            return False
        try:
            pipe = self._client.pipeline()
            for key, value in mapping.items():
                pipe.setex(key, ttl, value)
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis MSET error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._connected or self._client is None:
            return 0
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis CLEAR error: {e}")
            return 0


_redis: RedisCache | None = None


def get_redis_cache() -> RedisCache:
    """Get singleton Redis cache instance"""
    global _redis
    if _redis is None:
        _redis = RedisCache()
        _redis.connect()
    return _redis
