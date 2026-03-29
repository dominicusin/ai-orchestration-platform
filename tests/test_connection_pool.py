"""Tests for Connection Pool"""

import asyncio
from unittest.mock import MagicMock

import pytest

from orchestration.connection_pool import (
    ConnectionPool,
    HTTPConnectionPool,
    PoolConfig,
    PoolStats,
)


class TestPoolConfig:
    """Test PoolConfig"""

    def test_defaults(self):
        """Test default config"""
        config = PoolConfig()
        assert config.max_size == 10
        assert config.min_size == 2
        assert config.max_idle_time == 60.0
        assert config.acquire_timeout == 30.0
        assert config.retry_attempts == 3


class TestPoolStats:
    """Test PoolStats"""

    def test_avg_acquire_time(self):
        """Test avg acquire time calculation"""
        stats = PoolStats(acquired=10, total_acquire_time=5.0)
        assert stats.avg_acquire_time == 0.5

    def test_zero_acquires(self):
        """Test zero acquires"""
        stats = PoolStats()
        assert stats.avg_acquire_time == 0.0


class TestConnectionPool:
    """Test ConnectionPool"""

    @pytest.fixture
    def mock_factory(self):
        """Mock connection factory"""
        async def create():
            conn = MagicMock()
            conn.closed = False
            return conn
        return create

    @pytest.fixture
    def pool(self, mock_factory):
        """Create pool with mock factory"""
        config = PoolConfig(max_size=5, min_size=1)
        return ConnectionPool(mock_factory, config)

    @pytest.mark.asyncio
    async def test_pool_init(self, pool, mock_factory):
        """Test pool initialization"""
        assert pool.config.max_size == 5
        assert pool.config.min_size == 1

    @pytest.mark.asyncio
    async def test_start(self, pool):
        """Test pool start"""
        await pool.start()
        assert pool._running is True
        # Should create min connections
        await pool.stop()

    @pytest.mark.asyncio
    async def test_acquire(self, pool):
        """Test acquire connection"""
        await pool.start()
        conn = await pool.acquire()
        assert conn is not None
        assert pool.stats.active == 1
        await pool.release(conn)
        await pool.stop()

    @pytest.mark.asyncio
    async def test_acquire_release(self, pool):
        """Test acquire and release"""
        await pool.start()

        conn1 = await pool.acquire()
        conn2 = await pool.acquire()

        assert pool.stats.active == 2

        await pool.release(conn1)
        await pool.release(conn2)

        assert pool.stats.active == 0
        assert pool.stats.released == 2

        await pool.stop()

    @pytest.mark.asyncio
    async def test_concurrent_acquire(self, pool):
        """Test concurrent acquire"""
        await pool.start()

        async def acquire_and_release():
            conn = await pool.acquire()
            await asyncio.sleep(0.01)
            await pool.release(conn)

        # Acquire and release concurrently
        tasks = [acquire_and_release() for _ in range(5)]
        await asyncio.gather(*tasks)

        assert pool.stats.acquired == 5
        assert pool.stats.released == 5

        await pool.stop()

    @pytest.mark.asyncio
    async def test_release_invalid(self, pool):
        """Test release invalid connection"""
        await pool.start()

        conn = MagicMock()
        conn.closed = True

        await pool.release(conn)
        # Should not add to pool

        await pool.stop()

    @pytest.mark.asyncio
    async def test_get_stats(self, pool):
        """Test get stats"""
        await pool.start()
        stats = pool.get_stats()

        assert "size" in stats
        assert "active" in stats
        assert "idle" in stats
        assert "acquired" in stats

        await pool.stop()


class TestHTTPConnectionPool:
    """Test HTTPConnectionPool"""

    @pytest.mark.asyncio
    async def test_pool_creation(self):
        """Test HTTP pool creation"""
        pool = HTTPConnectionPool(PoolConfig(max_size=3, min_size=1))
        assert pool.config.max_size == 3

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test start and stop"""
        pool = HTTPConnectionPool(PoolConfig(max_size=2, min_size=0))
        await pool.start()
        assert pool._running is True
        await pool.stop()
        assert pool._running is False
