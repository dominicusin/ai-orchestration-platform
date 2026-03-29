"""Tests for Queues"""

import asyncio
import time

import pytest

from orchestration.queues import (
    DelayQueue,
    FIFOQueue,
    PriorityQueue,
    QueueItem,
    QueueManager,
    WorkQueue,
    get_queue_manager,
)


class TestQueueItem:
    """Test QueueItem"""

    def test_creation(self):
        """Test creation"""
        item = QueueItem(id="1", data="test", priority=5)
        assert item.id == "1"
        assert item.data == "test"
        assert item.priority == 5


class TestFIFOQueue:
    """Test FIFOQueue"""

    @pytest.fixture
    def queue(self):
        """Create queue"""
        return FIFOQueue()

    def test_creation(self, queue):
        """Test creation"""
        assert queue.empty() is True

    @pytest.mark.asyncio
    async def test_put_get(self, queue):
        """Test put and get"""
        item = QueueItem(id="1", data="test")
        await queue.put(item)

        assert queue.qsize() == 1
        assert queue.empty() is False

        received = await queue.get()
        assert received.id == "1"
        assert queue.empty() is True


class TestPriorityQueue:
    """Test PriorityQueue"""

    @pytest.fixture
    def queue(self):
        """Create queue"""
        return PriorityQueue()

    def test_creation(self, queue):
        """Test creation"""
        assert queue.empty() is True

    @pytest.mark.asyncio
    async def test_priority_order(self, queue):
        """Test priority order"""
        await queue.put(QueueItem(id="1", data="low", priority=1))
        await queue.put(QueueItem(id="2", data="high", priority=10))
        await queue.put(QueueItem(id="3", data="medium", priority=5))

        # Should get highest priority first
        item1 = await queue.get()
        assert item1.id == "2"  # priority 10

        item2 = await queue.get()
        assert item2.id == "3"  # priority 5

        item3 = await queue.get()
        assert item3.id == "1"  # priority 1


class TestDelayQueue:
    """Test DelayQueue"""

    @pytest.fixture
    def queue(self):
        """Create queue"""
        return DelayQueue()

    def test_creation(self, queue):
        """Test creation"""
        assert queue.empty() is True

    @pytest.mark.asyncio
    async def test_delay(self, queue):
        """Test delay"""
        await queue.put(QueueItem(id="1", data="test"), delay=0.1)

        start = time.time()
        item = await queue.get()
        elapsed = time.time() - start

        assert item.id == "1"
        assert elapsed >= 0.1


class TestWorkQueue:
    """Test WorkQueue"""

    @pytest.fixture
    def queue(self):
        """Create queue"""
        return FIFOQueue()

    @pytest.mark.asyncio
    async def test_worker(self, queue):
        """Test worker"""
        results = []

        def handler(item):
            results.append(item.data)

        work_queue = WorkQueue(queue, worker_count=1)
        work_queue.set_handler(handler)

        await work_queue.start()
        await queue.put(QueueItem(id="1", data="test1"))
        await queue.put(QueueItem(id="2", data="test2"))

        await asyncio.sleep(0.2)
        await work_queue.stop()

        assert len(results) >= 1


class TestQueueManager:
    """Test QueueManager"""

    @pytest.fixture
    def manager(self):
        """Create manager"""
        return QueueManager()

    def test_creation(self, manager):
        """Test creation"""
        assert manager is not None

    def test_create_fifo(self, manager):
        """Test create fifo"""
        queue = manager.create_fifo("test")
        assert isinstance(queue, FIFOQueue)

    def test_create_priority(self, manager):
        """Test create priority"""
        queue = manager.create_priority("test")
        assert isinstance(queue, PriorityQueue)

    def test_create_delay(self, manager):
        """Test create delay"""
        queue = manager.create_delay("test")
        assert isinstance(queue, DelayQueue)

    def test_get_queue(self, manager):
        """Test get queue"""
        manager.create_fifo("test")
        queue = manager.get_queue("test")
        assert queue is not None

    def test_delete_queue(self, manager):
        """Test delete queue"""
        manager.create_fifo("test")
        manager.delete_queue("test")
        assert manager.get_queue("test") is None

    def test_get_stats(self, manager):
        """Test get stats"""
        manager.create_fifo("q1")
        manager.create_priority("q2")
        stats = manager.get_stats()
        assert "q1" in stats
        assert "q2" in stats


class TestQueueManagerSingleton:
    """Test singleton"""

    def test_singleton(self):
        """Test singleton"""
        m1 = get_queue_manager()
        m2 = get_queue_manager()
        assert m1 is m2
