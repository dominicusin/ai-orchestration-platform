"""
Connection pool for HTTP clients
Пул соединений для HTTP клиентов с asyncio поддержкой
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import aiohttp

logger = logging.getLogger("orchestration.connection_pool")


@dataclass
class PoolConfig:
    """Конфигурация пула"""
    max_size: int = 10
    min_size: int = 2
    max_idle_time: float = 60.0
    acquire_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class PoolStats:
    """Статистика пула"""
    size: int = 0
    active: int = 0
    idle: int = 0
    acquired: int = 0
    released: int = 0
    errors: int = 0
    total_acquire_time: float = 0.0

    @property
    def avg_acquire_time(self) -> float:
        if self.acquired == 0:
            return 0.0
        return self.total_acquire_time / self.acquired


class ConnectionPool:
    """
    Пул соединений для aiohttp клиентов
    """

    def __init__(
        self,
        create_factory: Callable[[], Any],
        config: PoolConfig = None,
    ):
        self.create_factory = create_factory
        self.config = config or PoolConfig()

        self._pool: asyncio.Queue = asyncio.Queue(maxsize=self.config.max_size)
        self._created = 0
        self._active = 0
        self._lock = asyncio.Lock()

        self.stats = PoolStats()

        # Semaphore for limiting concurrent acquisitions
        self._semaphore = asyncio.Semaphore(self.config.max_size)

        # Background task for cleanup
        self._cleanup_task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        """Запуск пула"""
        self._running = True

        # Pre-create min connections
        for _ in range(self.config.min_size):
            conn = await self._create_connection()
            if conn:
                await self._pool.put(conn)

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info(f"Connection pool started: min={self.config.min_size}, max={self.config.max_size}")

    async def stop(self):
        """Остановка пула"""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                await self._close_connection(conn)
            except asyncio.QueueEmpty:
                break

        logger.info("Connection pool stopped")

    async def _create_connection(self) -> Any:
        """Создание нового соединения"""
        try:
            async with self._lock:
                if self._created >= self.config.max_size:
                    return None
                self._created += 1

            conn = await asyncio.wait_for(
                self.create_factory(),
                timeout=self.config.acquire_timeout,
            )
            self.stats.size = self._created
            return conn
        except Exception as e:
            logger.error(f"Error creating connection: {e}")
            self.stats.errors += 1
            return None

    async def _close_connection(self, conn: Any):
        """Закрытие соединения"""
        try:
            if hasattr(conn, "close"):
                await conn.close()
            async with self._lock:
                self._created -= 1
                self.stats.size = self._created
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")

    async def acquire(self) -> Any:
        """Получение соединения из пула"""
        start_time = time.time()

        async with self._semaphore:
            for attempt in range(self.config.retry_attempts):
                # Try to get from pool
                try:
                    conn = await asyncio.wait_for(
                        self._pool.get(),
                        timeout=self.config.acquire_timeout,
                    )
                    self.stats.idle -= 1
                    self.stats.active += 1
                    self.stats.acquired += 1
                    self.stats.total_acquire_time += time.time() - start_time
                    return conn
                except TimeoutError:
                    # Pool empty, try to create new
                    logger.debug(f"Pool empty, attempt {attempt + 1}")
                    if attempt < self.config.retry_attempts - 1:
                        await asyncio.sleep(self.config.retry_delay)
                        conn = await self._create_connection()
                        if conn:
                            self.stats.active += 1
                            self.stats.acquired += 1
                            self.stats.total_acquire_time += time.time() - start_time
                            return conn

            self.stats.errors += 1
            raise RuntimeError("Failed to acquire connection from pool")

    async def release(self, conn: Any):
        """Возвращение соединения в пул"""
        if conn is None:
            return

        self.stats.active -= 1
        self.stats.released += 1

        # Check if connection is still valid
        if await self._is_connection_valid(conn):
            try:
                self._pool.put_nowait(conn)
                self.stats.idle += 1
            except asyncio.QueueFull:
                # Pool full, close connection
                await self._close_connection(conn)
        else:
            await self._close_connection(conn)

    async def _is_connection_valid(self, conn: Any) -> bool:
        """Проверка валидности соединения"""
        try:
            if hasattr(conn, "closed") and conn.closed:
                return False
            if hasattr(conn, "is_closed") and conn.is_closed:
                return False
            return True
        except Exception:
            return False

    async def _cleanup_loop(self):
        """Фоновый процесс очистки"""
        while self._running:
            try:
                await asyncio.sleep(10)

                # Close excess idle connections
                while self.stats.idle > self.config.min_size:
                    try:
                        conn = self._pool.get_nowait()
                        await self._close_connection(conn)
                        self.stats.idle -= 1
                    except asyncio.QueueEmpty:
                        break

                # Close stale connections
                if not self._pool.empty():
                    conn = self._pool.queue[0]
                    # Could add stale check here

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Cleanup error: {e}")

    def get_stats(self) -> dict:
        """Получение статистики пула"""
        return {
            "size": self.stats.size,
            "active": self.stats.active,
            "idle": self.stats.idle,
            "acquired": self.stats.acquired,
            "released": self.stats.released,
            "errors": self.stats.errors,
            "avg_acquire_time": f"{self.stats.avg_acquire_time:.3f}s",
        }


class HTTPConnectionPool(ConnectionPool):
    """
    Пул для aiohttp клиентов
    """

    def __init__(self, config: PoolConfig = None):
        super().__init__(self._create_aiohttp_session, config)

    async def _create_aiohttp_session(self) -> aiohttp.ClientSession:
        """Создание aiohttp сессии"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_size,
            limit_per_host=self.config.max_size,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        return aiohttp.ClientSession(connector=connector)


# Singleton
_http_pool: HTTPConnectionPool | None = None


def get_http_pool(config: PoolConfig = None) -> HTTPConnectionPool:
    """Получение HTTP пула"""
    global _http_pool
    if _http_pool is None:
        _http_pool = HTTPConnectionPool(config)
    return _http_pool
