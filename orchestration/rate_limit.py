"""
Rate limiter
Ограничитель частоты запросов
"""

import asyncio
import time

from orchestration.retry import TokenBucket


def rate_limited(rate: int, per_seconds: float = 1.0):
    """Декоратор для ограничения частоты вызовов"""
    limiter = RateLimiter(rate, per_seconds)

    def decorator(func):
        async def wrapper(*args, **kwargs):
            await limiter.acquire()
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator


class RateLimiter:
    """
    Ограничитель частоты с использованием token bucket
    """

    def __init__(self, rate: int, per_seconds: float = 1.0):
        self.rate = rate
        self.per_seconds = per_seconds
        self._bucket = TokenBucket(rate, rate)
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1):
        """Получение токена"""
        while True:
            if self._bucket.try_consume(tokens):
                return
            await asyncio.sleep(0.01)

    def try_acquire(self, tokens: int = 1) -> bool:
        """Попытка получения токена без ожидания"""
        return self._bucket.try_consume(tokens)


class SlidingWindowRateLimiter:
    """
    Rate limiter с скользящим окном
    """

    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Получение доступа"""
        async with self._lock:
            now = time.time()
            # Remove old requests
            self._requests = [
                t for t in self._requests
                if now - t < self.window_seconds
            ]

            if len(self._requests) >= self.max_requests:
                # Calculate wait time
                oldest = self._requests[0]
                wait_time = self.window_seconds - (now - oldest)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    self._requests = [
                        t for t in self._requests
                        if now - t < self.window_seconds
                    ]

            self._requests.append(now)

    def try_acquire(self) -> bool:
        """Попытка без ожидания"""
        now = time.time()
        self._requests = [
            t for t in self._requests
            if now - t < self.window_seconds
        ]

        if len(self._requests) < self.max_requests:
            self._requests.append(now)
            return True
        return False


class PerKeyRateLimiter:
    """
    Rate limiter с разными лимитами для разных ключей
    """

    def __init__(self, default_rate: int, per_seconds: float = 60.0):
        self.default_rate = default_rate
        self.per_seconds = per_seconds
        self._limiters: dict[str, SlidingWindowRateLimiter] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, key: str, rate: int = None):
        """Получение доступа для ключа"""
        rate = rate or self.default_rate

        async with self._lock:
            if key not in self._limiters:
                self._limiters[key] = SlidingWindowRateLimiter(
                    rate, self.per_seconds
                )

        await self._limiters[key].acquire()

    def try_acquire(self, key: str, rate: int = None) -> bool:
        """Попытка без ожидания"""
        rate = rate or self.default_rate

        if key not in self._limiters:
            self._limiters[key] = SlidingWindowRateLimiter(rate, self.per_seconds)

        return self._limiters[key].try_acquire()
