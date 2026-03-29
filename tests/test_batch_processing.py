"""Tests for Batch Processing"""

import asyncio

import pytest

from orchestration.batch_processing import (
    BatchItem,
    BatchProcessor,
    BatchQueue,
    BatchResult,
    ChunkedIterator,
    RateLimiter,
)


class TestBatchItem:
    """Test BatchItem"""

    def test_creation(self):
        """Test creation"""
        item = BatchItem(
            id="item-1",
            data={"key": "value"},
            priority=5,
        )
        assert item.id == "item-1"
        assert item.data["key"] == "value"
        assert item.priority == 5


class TestBatchResult:
    """Test BatchResult"""

    def test_creation(self):
        """Test creation"""
        result = BatchResult(
            batch_id="batch-1",
            total=10,
            successful=8,
            failed=2,
            duration=1.5,
        )
        assert result.batch_id == "batch-1"
        assert result.total == 10
        assert result.successful == 8


class TestBatchProcessor:
    """Test BatchProcessor"""

    @pytest.fixture
    def processor(self):
        """Create processor"""
        return BatchProcessor(max_concurrent=2, max_retries=2, batch_size=5)

    def test_creation(self, processor):
        """Test creation"""
        assert processor.max_concurrent == 2
        assert processor.max_retries == 2
        assert processor.batch_size == 5

    @pytest.mark.asyncio
    async def test_process_batch(self, processor):
        """Test process batch"""
        items = [
            BatchItem(id=f"item-{i}", data=i) for i in range(5)
        ]

        async def simple_processor(item):
            await asyncio.sleep(0.01)

        result = await processor.process_batch(items, simple_processor)
        assert result.total == 5

    @pytest.mark.asyncio
    async def test_process_batch_with_errors(self, processor):
        """Test batch with errors"""
        items = [
            BatchItem(id="item-1", data=1),
            BatchItem(id="item-2", data="error"),
            BatchItem(id="item-3", data=3),
        ]

        def failing_processor(item):
            if item.data == "error":
                raise ValueError("Test error")

        result = await processor.process_batch(items, failing_processor)
        assert result.total == 3

    @pytest.mark.asyncio
    async def test_process_in_chunks(self, processor):
        """Test process in chunks"""
        items = [BatchItem(id=f"item-{i}", data=i) for i in range(12)]

        async def simple_processor(item):
            pass

        results = await processor.process_in_chunks(items, simple_processor)
        assert len(results) == 3  # 12 / 5 = 3 chunks


class TestChunkedIterator:
    """Test ChunkedIterator"""

    def test_iteration(self):
        """Test iteration"""
        data = list(range(10))
        iterator = ChunkedIterator(data, chunk_size=3)

        chunks = list(iterator)
        assert len(chunks) == 4  # 10 / 3 = 4
        assert chunks[0] == [0, 1, 2]
        assert chunks[-1] == [9]

    def test_len(self):
        """Test len"""
        data = list(range(10))
        iterator = ChunkedIterator(data, chunk_size=3)
        assert len(iterator) == 4


class TestRateLimiter:
    """Test RateLimiter"""

    @pytest.mark.asyncio
    async def test_acquire(self):
        """Test acquire"""
        limiter = RateLimiter(rate=10, per_seconds=1.0)
        # Should not raise
        await limiter.acquire()

    @pytest.mark.asyncio
    async def test_multiple_acquires(self):
        """Test multiple acquires"""
        limiter = RateLimiter(rate=5, per_seconds=1.0)
        for _ in range(5):
            await limiter.acquire()


class TestBatchQueue:
    """Test BatchQueue"""

    @pytest.fixture
    def queue(self):
        """Create queue"""
        return BatchQueue()

    @pytest.mark.asyncio
    async def test_put(self, queue):
        """Test put"""
        item = BatchItem(id="item-1", data={})
        await queue.put(item)
        assert queue.size() == 1

    @pytest.mark.asyncio
    async def test_put_many(self, queue):
        """Test put many"""
        items = [BatchItem(id=f"item-{i}", data=i) for i in range(5)]
        await queue.put_many(items)
        assert queue.size() == 5

    @pytest.mark.asyncio
    async def test_get(self, queue):
        """Test get"""
        items = [BatchItem(id=f"item-{i}", data=i) for i in range(5)]
        await queue.put_many(items)

        retrieved = await queue.get(2)
        assert len(retrieved) == 2
        assert queue.size() == 3

    @pytest.mark.asyncio
    async def test_priority_order(self, queue):
        """Test priority ordering"""
        items = [
            BatchItem(id="low", data=1, priority=1),
            BatchItem(id="high", data=2, priority=10),
            BatchItem(id="medium", data=3, priority=5),
        ]
        await queue.put_many(items)

        first = await queue.get(1)
        assert first[0].id == "high"

    def test_is_empty(self, queue):
        """Test is_empty"""
        assert queue.is_empty() is True
