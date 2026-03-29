"""
Batch processing utilities
Утилиты для пакетной обработки данных
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("orchestration.batch")


@dataclass
class BatchItem:
    """Элемент батча"""
    id: str
    data: Any
    priority: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class BatchResult:
    """Результат обработки батча"""
    batch_id: str
    total: int
    successful: int
    failed: int
    duration: float
    errors: list[dict] = field(default_factory=list)


class BatchProcessor:
    """
    Процессор батчей с поддержкой:
    - Параллельная обработка
    - Ограничение concurrency
    - Retry логика
    - Progress tracking
    """

    def __init__(
        self,
        max_concurrent: int = 4,
        max_retries: int = 3,
        batch_size: int = 10,
    ):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.batch_size = batch_size
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def process_batch(
        self,
        items: list[BatchItem],
        processor: Callable,
        batch_id: str = None,
    ) -> BatchResult:
        """Обработка батча"""
        batch_id = batch_id or f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        successful = 0
        failed = 0
        errors = []

        async def process_item(item: BatchItem) -> bool:
            nonlocal successful, failed

            for attempt in range(self.max_retries):
                try:
                    async with self._semaphore:
                        if asyncio.iscoroutinefunction(processor):
                            await processor(item)
                        else:
                            processor(item)
                    successful += 1
                    return True
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.debug(f"Retry {attempt + 1} for {item.id}")
                        await asyncio.sleep(0.5 * (attempt + 1))
                    else:
                        failed += 1
                        errors.append({
                            "item_id": item.id,
                            "error": str(e),
                            "attempt": attempt + 1,
                        })
                        logger.error(f"Failed to process {item.id}: {e}")
            return False

        # Process all items
        tasks = [process_item(item) for item in items]
        await asyncio.gather(*tasks, return_exceptions=True)

        duration = (datetime.now() - start_time).total_seconds()

        return BatchResult(
            batch_id=batch_id,
            total=len(items),
            successful=successful,
            failed=failed,
            duration=duration,
            errors=errors,
        )

    async def process_in_chunks(
        self,
        items: list[BatchItem],
        processor: Callable,
    ) -> list[BatchResult]:
        """Обработка батчей по чанкам"""
        results = []

        # Sort by priority (highest first)
        sorted_items = sorted(items, key=lambda x: x.priority, reverse=True)

        # Split into chunks
        chunks = [
            sorted_items[i:i + self.batch_size]
            for i in range(0, len(sorted_items), self.batch_size)
        ]

        logger.info(f"Processing {len(items)} items in {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i + 1}/{len(chunks)}")
            result = await self.process_batch(
                chunk,
                processor,
                batch_id=f"chunk_{i + 1}",
            )
            results.append(result)

        return results


class ChunkedIterator:
    """
    Итератор по чанкам
    """

    def __init__(self, data: list, chunk_size: int = 10):
        self.data = data
        self.chunk_size = chunk_size

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> list:
        if self._index >= len(self.data):
            raise StopIteration

        chunk = self.data[self._index:self._index + self.chunk_size]
        self._index += self.chunk_size
        return chunk

    def __len__(self) -> int:
        return (len(self.data) + self.chunk_size - 1) // self.chunk_size


class RateLimiter:
    """
    Ограничитель скорости
    """

    def __init__(self, rate: int, per_seconds: float = 1.0):
        self.rate = rate
        self.per_seconds = per_seconds
        self._tokens = rate
        self._last_update = datetime.now()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Получение токена"""
        async with self._lock:
            now = datetime.now()
            elapsed = (now - self._last_update).total_seconds()

            # Refill tokens
            self._tokens = min(
                self.rate,
                self._tokens + elapsed * (self.rate / self.per_seconds)
            )
            self._last_update = now

            if self._tokens < 1:
                wait_time = (1 - self._tokens) * (self.per_seconds / self.rate)
                await asyncio.sleep(wait_time)
                self._tokens = 0
            else:
                self._tokens -= 1


class BatchQueue:
    """
    Очередь батчей с приоритетами
    """

    def __init__(self):
        self._queue: list[BatchItem] = []
        self._lock = asyncio.Lock()

    async def put(self, item: BatchItem):
        """Добавление элемента"""
        async with self._lock:
            self._queue.append(item)
            # Sort by priority
            self._queue.sort(key=lambda x: x.priority, reverse=True)

    async def put_many(self, items: list[BatchItem]):
        """Добавление нескольких элементов"""
        async with self._lock:
            self._queue.extend(items)
            self._queue.sort(key=lambda x: x.priority, reverse=True)

    async def get(self, count: int = 1) -> list[BatchItem]:
        """Получение элементов"""
        async with self._lock:
            items = self._queue[:count]
            self._queue = self._queue[count:]
            return items

    async def get_batch(self, size: int = 10) -> list[BatchItem]:
        """Получение батча"""
        return await self.get(size)

    def size(self) -> int:
        """Размер очереди"""
        return len(self._queue)

    def is_empty(self) -> bool:
        """Проверка пустоты"""
        return len(self._queue) == 0
