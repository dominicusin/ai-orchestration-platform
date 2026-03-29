"""
Locks for distributed coordination
Блокировки для распределённой координации
"""

import asyncio
import time


class Lock:
    """Базовый класс блокировки"""

    async def acquire(self, timeout: float = None) -> bool:
        """Получение блокировки"""
        raise NotImplementedError

    async def release(self):
        """Освобождение блокировки"""
        raise NotImplementedError

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        await self.release()


class AsyncLock(Lock):
    """Асинхронная блокировка"""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._holder = None
        self._acquired_at = None

    async def acquire(self, timeout: float = None) -> bool:
        """Получение блокировки"""
        try:
            if timeout:
                await asyncio.wait_for(self._lock.acquire(), timeout=timeout)
            else:
                await self._lock.acquire()

            self._holder = id(asyncio.current_task())
            self._acquired_at = time.time()
            return True
        except TimeoutError:
            return False

    async def release(self):
        """Освобождение блокировки"""
        self._lock.release()
        self._holder = None
        self._acquired_at = None

    def is_locked(self) -> bool:
        """Проверка занятости"""
        return self._lock.locked()

    def holder(self) -> int | None:
        """Получение ID владельца"""
        return self._holder

    def duration(self) -> float | None:
        """Длительность удержания"""
        if self._acquired_at:
            return time.time() - self._acquired_at
        return None


class Semaphore(Lock):
    """Семафор"""

    def __init__(self, value: int = 1):
        self._semaphore = asyncio.Semaphore(value)
        self._value = value

    async def acquire(self, timeout: float = None) -> bool:
        """Получение"""
        try:
            if timeout:
                await asyncio.wait_for(self._semaphore.acquire(), timeout=timeout)
            else:
                await self._semaphore.acquire()
            return True
        except TimeoutError:
            return False

    async def release(self):
        """Освобождение"""
        self._semaphore.release()

    def available(self) -> int:
        """Доступное количество"""
        return self._semaphore._value


class RWLock(Lock):
    """Блокировка чтения-записи"""

    def __init__(self):
        self._readers = 0
        self._writer = False
        self._lock = asyncio.Lock()
        self._read_ready = asyncio.Condition(self._lock)

    async def acquire_read(self):
        """Получение блокировки чтения"""
        async with self._lock:
            while self._writer:
                await self._read_ready.wait()
            self._readers += 1

    async def release_read(self):
        """Освобождение блокировки чтения"""
        async with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    async def acquire_write(self):
        """Получение блокировки записи"""
        async with self._lock:
            while self._readers > 0 or self._writer:
                await self._read_ready.wait()
            self._writer = True

    async def release_write(self):
        """Освобождение блокировки записи"""
        async with self._lock:
            self._writer = False
            self._read_ready.notify_all()

    async def acquire(self, timeout: float = None) -> bool:
        """По умолчанию acquire для записи"""
        return await self.acquire_write()

    async def release(self):
        """Освобождение"""
        await self.release_write()

    def is_writing(self) -> bool:
        """Идёт запись?"""
        return self._writer

    def reader_count(self) -> int:
        """Количество читателей"""
        return self._readers


class LockManager:
    """Менеджер блокировок"""

    def __init__(self):
        self._locks: dict[str, AsyncLock] = {}

    def get_lock(self, name: str) -> AsyncLock:
        """Получение блокировки по имени"""
        if name not in self._locks:
            self._locks[name] = AsyncLock()
        return self._locks[name]

    async def acquire(self, name: str, timeout: float = None) -> bool:
        """Получение блокировки"""
        lock = self.get_lock(name)
        return await lock.acquire(timeout)

    async def release(self, name: str):
        """Освобождение блокировки"""
        if name in self._locks:
            await self._locks[name].release()

    def is_locked(self, name: str) -> bool:
        """Проверка занятости"""
        if name not in self._locks:
            return False
        return self._locks[name].is_locked()

    def get_stats(self) -> dict:
        """Статистика"""
        return {
            name: {
                "locked": lock.is_locked(),
                "holder": lock.holder(),
                "duration": lock.duration(),
            }
            for name, lock in self._locks.items()
        }


# Singleton
_lock_manager: LockManager | None = None


def get_lock_manager() -> LockManager:
    """Получение менеджера блокировок"""
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = LockManager()
    return _lock_manager
