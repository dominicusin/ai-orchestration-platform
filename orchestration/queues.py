"""
Queues for task processing
Очереди для обработки задач
"""

import asyncio
import heapq
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueueItem:
    """Элемент очереди"""
    id: str
    data: Any
    priority: int = 0
    created_at: float = field(default_factory=time.time)
    retries: int = 0
    metadata: dict = field(default_factory=dict)


class Queue:
    """Базовый класс очереди"""

    async def put(self, item: QueueItem):
        """Добавление элемента"""
        raise NotImplementedError

    async def get(self) -> QueueItem:
        """Получение элемента"""
        raise NotImplementedError

    def qsize(self) -> int:
        """Размер очереди"""
        raise NotImplementedError

    def empty(self) -> bool:
        """Проверка пустоты"""
        raise NotImplementedError


class FIFOQueue(Queue):
    """Очередь FIFO"""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()

    async def put(self, item: QueueItem):
        """Добавление"""
        await self._queue.put(item)

    async def get(self) -> QueueItem:
        """Получение"""
        return await self._queue.get()

    def qsize(self) -> int:
        """Размер"""
        return self._queue.qsize()

    def empty(self) -> bool:
        """Пуста?"""
        return self._queue.empty()


class PriorityQueue(Queue):
    """Очередь с приоритетами"""

    def __init__(self):
        self._heap: list = []
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)

    async def put(self, item: QueueItem):
        """Добавление"""
        async with self._lock:
            # (-priority, created_at, id) for min-heap
            heapq.heappush(self._heap, (-item.priority, item.created_at, item.id, item))
            self._not_empty.notify()

    async def get(self) -> QueueItem:
        """Получение"""
        async with self._not_empty:
            while not self._heap:
                await self._not_empty.wait()

            _, _, _, item = heapq.heappop(self._heap)
            return item

    def qsize(self) -> int:
        """Размер"""
        return len(self._heap)

    def empty(self) -> bool:
        """Пуста?"""
        return len(self._heap) == 0


class DelayQueue(Queue):
    """Очередь с задержкой"""

    def __init__(self):
        self._queue: list = []
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)

    async def put(self, item: QueueItem, delay: float = 0):
        """Добавление с задержкой"""
        async with self._lock:
            available_at = time.time() + delay
            heapq.heappush(self._queue, (available_at, item))
            self._not_empty.notify()

    async def get(self) -> QueueItem:
        """Получение"""
        async with self._not_empty:
            while not self._queue:
                await self._not_empty.wait()

            available_at, item = self._queue[0]
            now = time.time()

            if available_at > now:
                await asyncio.sleep(available_at - now)

            _, item = heapq.heappop(self._queue)
            return item

    def qsize(self) -> int:
        """Размер"""
        return len(self._queue)

    def empty(self) -> bool:
        """Пуста?"""
        return len(self._queue) == 0


class WorkQueue:
    """Очередь с воркерами"""

    def __init__(self, queue: Queue, worker_count: int = 1):
        self.queue = queue
        self.worker_count = worker_count
        self._workers: list = []
        self._running = False
        self._handler: Callable | None = None

    def set_handler(self, handler: Callable):
        """Установка обработчика"""
        self._handler = handler

    async def start(self):
        """Запуск воркеров"""
        self._running = True
        self._workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.worker_count)
        ]

    async def stop(self):
        """Остановка воркеров"""
        self._running = False
        for worker in self._workers:
            worker.cancel()
        self._workers.clear()

    async def _worker(self, worker_id: int):
        """Воркер"""
        while self._running:
            try:
                item = await self.queue.get()

                if self._handler:
                    if asyncio.iscoroutinefunction(self._handler):
                        await self._handler(item)
                    else:
                        self._handler(item)

            except asyncio.CancelledError:
                break
            except Exception:
                pass


class QueueManager:
    """Менеджер очередей"""

    def __init__(self):
        self._queues: dict[str, Queue] = {}

    def create_fifo(self, name: str) -> FIFOQueue:
        """Создание FIFO очереди"""
        queue = FIFOQueue()
        self._queues[name] = queue
        return queue

    def create_priority(self, name: str) -> PriorityQueue:
        """Создание приоритетной очереди"""
        queue = PriorityQueue()
        self._queues[name] = queue
        return queue

    def create_delay(self, name: str) -> DelayQueue:
        """Создание очереди с задержкой"""
        queue = DelayQueue()
        self._queues[name] = queue
        return queue

    def get_queue(self, name: str) -> Queue | None:
        """Получение очереди"""
        return self._queues.get(name)

    def delete_queue(self, name: str):
        """Удаление очереди"""
        if name in self._queues:
            del self._queues[name]

    def get_stats(self) -> dict:
        """Статистика"""
        return {
            name: {"size": queue.qsize(), "empty": queue.empty()}
            for name, queue in self._queues.items()
        }


# Singleton
_queue_manager: QueueManager | None = None


def get_queue_manager() -> QueueManager:
    """Получение менеджера очередей"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = QueueManager()
    return _queue_manager
