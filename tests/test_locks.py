"""Tests for Locks"""


import pytest

from orchestration.locks import (
    AsyncLock,
    LockManager,
    RWLock,
    Semaphore,
    get_lock_manager,
)


class TestAsyncLock:
    """Test AsyncLock"""

    @pytest.fixture
    def lock(self):
        """Create lock"""
        return AsyncLock()

    def test_creation(self, lock):
        """Test creation"""
        assert lock is not None

    @pytest.mark.asyncio
    async def test_acquire_release(self, lock):
        """Test acquire and release"""
        assert await lock.acquire() is True
        assert lock.is_locked() is True

        await lock.release()
        assert lock.is_locked() is False

    @pytest.mark.asyncio
    async def test_context_manager(self, lock):
        """Test context manager"""
        async with lock:
            assert lock.is_locked() is True

        assert lock.is_locked() is False

    @pytest.mark.asyncio
    async def test_timeout(self, lock):
        """Test timeout"""
        await lock.acquire()
        result = await lock.acquire(timeout=0.1)
        assert result is False
        await lock.release()


class TestSemaphore:
    """Test Semaphore"""

    @pytest.fixture
    def sem(self):
        """Create semaphore"""
        return Semaphore(2)

    def test_creation(self, sem):
        """Test creation"""
        assert sem._value == 2

    @pytest.mark.asyncio
    async def test_acquire_release(self, sem):
        """Test acquire and release"""
        assert await sem.acquire() is True
        assert await sem.acquire() is True

        await sem.release()
        await sem.release()

    @pytest.mark.asyncio
    async def test_available(self, sem):
        """Test available"""
        assert sem.available() == 2
        await sem.acquire()
        assert sem.available() == 1


class TestRWLock:
    """Test RWLock"""

    @pytest.fixture
    def rwlock(self):
        """Create rwlock"""
        return RWLock()

    def test_creation(self, rwlock):
        """Test creation"""
        assert rwlock._readers == 0
        assert rwlock.is_writing() is False

    @pytest.mark.asyncio
    async def test_readers(self, rwlock):
        """Test readers"""
        await rwlock.acquire_read()
        assert rwlock.reader_count() == 1
        await rwlock.release_read()
        assert rwlock.reader_count() == 0

    @pytest.mark.asyncio
    async def test_writer(self, rwlock):
        """Test writer"""
        await rwlock.acquire_write()
        assert rwlock.is_writing() is True
        await rwlock.release_write()
        assert rwlock.is_writing() is False


class TestLockManager:
    """Test LockManager"""

    @pytest.fixture
    def manager(self):
        """Create manager"""
        return LockManager()

    def test_creation(self, manager):
        """Test creation"""
        assert manager is not None

    def test_get_lock(self, manager):
        """Test get lock"""
        lock1 = manager.get_lock("test")
        lock2 = manager.get_lock("test")
        assert lock1 is lock2

    @pytest.mark.asyncio
    async def test_acquire_release(self, manager):
        """Test acquire release"""
        assert await manager.acquire("lock1") is True
        assert manager.is_locked("lock1") is True

        await manager.release("lock1")
        assert manager.is_locked("lock1") is False

    def test_get_stats(self, manager):
        """Test get stats"""
        manager.get_lock("lock1")
        stats = manager.get_stats()
        assert "lock1" in stats


class TestLockManagerSingleton:
    """Test singleton"""

    def test_singleton(self):
        """Test singleton"""
        m1 = get_lock_manager()
        m2 = get_lock_manager()
        assert m1 is m2
