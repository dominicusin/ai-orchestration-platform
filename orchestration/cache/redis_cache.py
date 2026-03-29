"""
Redis cache для распределённого кэширования
Обеспечивает shared cache между несколькими инстансами приложения.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import redis

from .cache import CachePolicy, CacheStats

logger = logging.getLogger("orchestration.cache.redis")


class RedisCacheError(Exception):
    """Ошибка Redis кэша"""
    pass


@dataclass
class RedisCacheConfig:
    """Конфигурация Redis кэша"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    ssl: bool = False
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    max_connections: int = 10
    decode_responses: bool = True

    # Key prefixes
    key_prefix: str = "ai_pipeline:"

    # TTL по умолчанию (секунды)
    default_ttl: int = 86400 * 7  # 7 дней

    @classmethod
    def from_env(cls) -> "RedisCacheConfig":
        import os
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
            key_prefix=os.getenv("REDIS_KEY_PREFIX", "ai_pipeline:"),
            default_ttl=int(os.getenv("REDIS_TTL", str(86400 * 7))),
        )


class RedisCache:
    """
    Redis-based distributed cache с:
    - Pipeline integration (fallback на file cache)
    - Pub/Sub для инвалидации между инстансами
    - Lua scripts для атомарных операций
    - Connection pooling
    """

    def __init__(
        self,
        config: RedisCacheConfig = None,
        policy: CachePolicy = CachePolicy.CACHE_FIRST,
        local_cache_dir: Path = None,
    ):
        self.config = config or RedisCacheConfig.from_env()
        self.policy = policy
        self.local_cache_dir = local_cache_dir

        # Redis клиент
        self._client: redis.Redis | None = None
        self._connected = False

        # Fallback на локальный кэш
        self._local_cache = None
        if local_cache_dir:
            from .cache import FileCache
            self._local_cache = FileCache(local_cache_dir, policy)

        # Статистика
        self.stats = CacheStats()

        # Lua script для атомарного get_or_set
        self._get_or_set_script = """
        local key = KEYS[1]
        local value = redis.call('GET', key)
        if value then
            return value
        end
        return nil
        """

    def connect(self) -> bool:
        """Подключение к Redis"""
        try:
            self._client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                ssl=self.config.ssl,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                max_connections=self.config.max_connections,
                decode_responses=self.config.decode_responses,
                health_check_interval=30,
            )
            # Проверка соединения
            self._client.ping()
            self._connected = True
            logger.info(f"✅ Redis connected: {self.config.host}:{self.config.port}")
            return True
        except redis.ConnectionError as e:
            logger.warning(f"❌ Redis connection failed: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Redis error: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """Отключение от Redis"""
        if self._client:
            try:
                self._client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis: {e}")
        self._connected = False

    def _get_key(self, source_path: str, operation: str) -> str:
        """Генерация ключа для Redis"""
        key_hash = hashlib.sha256(
            f"{operation}:{source_path}".encode()
        ).hexdigest()[:16]
        return f"{self.config.key_prefix}{operation}:{key_hash}"

    def _get_source_hash(self, source_content: str) -> str:
        """Хэш содержимого источника"""
        return hashlib.md5(source_content.encode()).hexdigest()

    def get(
        self,
        source_path: str,
        operation: str,
        source_content: str
    ) -> str | None:
        """
        Получение результата из Redis кэша
        """
        if self.policy == CachePolicy.SKIP_CACHE:
            return None

        source_hash = self._get_source_hash(source_content)
        key = self._get_key(source_path, operation)

        # Пробуем Redis
        if self._connected and self._client:
            try:
                # Получаем значение и хэш
                value = self._client.hget(key, "result")
                stored_hash = self._client.hget(key, "source_hash")

                if value and stored_hash == source_hash:
                    self.stats.hits += 1
                    logger.debug(f"Redis hit: {source_path}:{operation}")
                    return value
            except redis.RedisError as e:
                logger.warning(f"Redis get error: {e}")
                self.stats.errors += 1

        # Fallback на локальный кэш
        if self._local_cache:
            return self._local_cache.get(source_path, operation, source_content)

        self.stats.misses += 1
        return None

    def set(
        self,
        source_path: str,
        operation: str,
        source_content: str,
        result: str,
        ttl: int = None,
        metadata: dict[str, Any] = None,
    ):
        """Сохранение результата в Redis"""
        source_hash = self._get_source_hash(source_content)
        key = self._get_key(source_path, operation)
        ttl = ttl or self.config.default_ttl

        # Сохраняем в Redis
        if self._connected and self._client:
            try:
                pipe = self._client.pipeline()
                pipe.hset(key, mapping={
                    "result": result,
                    "source_hash": source_hash,
                    "operation": operation,
                    "source_path": source_path,
                    "timestamp": str(time.time()),
                    "metadata": json.dumps(metadata or {}),
                })
                pipe.expire(key, ttl)
                pipe.execute()
                self.stats.writes += 1
                logger.debug(f"Redis set: {source_path}:{operation}")

                # Публикуем инвалидацию
                self._publish_invalidation(operation, source_path)

            except redis.RedisError as e:
                logger.warning(f"Redis set error: {e}")
                self.stats.errors += 1

        # Fallback на локальный кэш
        if self._local_cache:
            self._local_cache.set(source_path, operation, source_content, result, metadata)

    def _publish_invalidation(self, operation: str, source_path: str):
        """Публикация события инвалидации"""
        try:
            channel = f"{self.config.key_prefix}invalidation"
            message = json.dumps({
                "operation": operation,
                "source_path": source_path,
                "timestamp": time.time(),
            })
            self._client.publish(channel, message)
        except redis.RedisError as e:
            logger.debug(f"Redis publish error: {e}")

    def subscribe_invalidation(self, callback):
        """Подписка на события инвалидации"""
        if not self._connected:
            return

        pubsub = self._client.pubsub()
        channel = f"{self.config.key_prefix}invalidation"
        pubsub.subscribe(channel)

        def listener():
            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        callback(data)
                    except Exception as e:
                        logger.warning(f"Invalidation callback error: {e}")

        import threading
        thread = threading.Thread(target=listener, daemon=True)
        thread.start()
        return pubsub

    def invalidate(self, source_path: str = None, operation: str = None):
        """Инвалидация кэша"""
        if not self._connected:
            return

        try:
            if source_path and operation:
                key = self._get_key(source_path, operation)
                self._client.delete(key)
                self._publish_invalidation(operation, source_path)
                self.stats.invalidations += 1

            elif operation:
                # Инвалидация всех записей для операции
                pattern = f"{self.config.key_prefix}{operation}:*"
                keys = self._client.keys(pattern)
                if keys:
                    self._client.delete(*keys)
                    self.stats.invalidations += len(keys)

        except redis.RedisError as e:
            logger.warning(f"Redis invalidate error: {e}")
            self.stats.errors += 1

        # Fallback
        if self._local_cache:
            self._local_cache.invalidate(source_path, operation)

    def clear(self):
        """Очистка всего кэша"""
        if self._connected and self._client:
            try:
                pattern = f"{self.config.key_prefix}*"
                keys = self._client.keys(pattern)
                if keys:
                    self._client.delete(*keys)
                self.stats.invalidations += 1
            except redis.RedisError as e:
                logger.warning(f"Redis clear error: {e}")

        if self._local_cache:
            self._local_cache.clear()

        logger.info("Redis cache cleared")

    def get_stats(self) -> dict:
        """Получение статистики"""
        stats = {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "writes": self.stats.writes,
            "invalidations": self.stats.invalidations,
            "errors": self.stats.errors,
            "hit_rate": self.stats.hit_rate,
            "connected": self._connected,
            "redis_host": f"{self.config.host}:{self.config.port}",
        }

        if self._local_cache:
            local_stats = self._local_cache.get_stats()
            stats["local_cache"] = local_stats

        return stats

    def get_redis_info(self) -> dict | None:
        """Получение информации о Redis сервере"""
        if not self._connected:
            return None

        try:
            info = self._client.info()
            return {
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime": info.get("uptime_in_days"),
            }
        except redis.RedisError as e:
            logger.warning(f"Redis info error: {e}")
            return None


# Singleton
_redis_cache: RedisCache | None = None


def get_redis_cache(
    config: RedisCacheConfig = None,
    policy: CachePolicy = CachePolicy.CACHE_FIRST,
    local_cache_dir: Path = None,
) -> RedisCache:
    """Получение инстанса Redis кэша"""
    global _redis_cache

    if _redis_cache is None:
        _redis_cache = RedisCache(config, policy, local_cache_dir)
        _redis_cache.connect()

    return _redis_cache


def create_redis_cache(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: str | None = None,
) -> RedisCache:
    """Создание нового инстанса Redis кэша"""
    config = RedisCacheConfig(
        host=host,
        port=port,
        db=db,
        password=password,
    )
    cache = RedisCache(config)
    cache.connect()
    return cache
