"""
Timing utilities
Утилиты для измерения времени
"""

import functools
import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class TimingResult:
    """Результат замера времени"""
    name: str
    duration: float
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)


class Timer:
    """Таймер"""

    def __init__(self, name: str = "timer"):
        self.name = name
        self._start = None
        self._end = None

    def start(self):
        """Запуск"""
        self._start = time.time()
        return self

    def stop(self) -> float:
        """Остановка"""
        self._end = time.time()
        return self.elapsed()

    def elapsed(self) -> float:
        """Прошедшее время"""
        if self._start is None:
            return 0.0
        end = self._end if self._end else time.time()
        return end - self._start

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


def timed(func: Callable) -> Callable:
    """Декоратор для замера времени"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.4f}s")
        return result
    return wrapper


def async_timed(func: Callable) -> Callable:
    """Декоратор для замера времени async функций"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.4f}s")
        return result
    return wrapper


class Stopwatch:
    """Секундомер с несколькими кругами"""

    def __init__(self):
        self._start_time = None
        self._laps = []

    def start(self):
        """Запуск"""
        self._start_time = time.time()
        self._laps = []
        return self

    def lap(self) -> float:
        """Круг"""
        if self._start_time is None:
            return 0.0
        lap_time = time.time() - self._start_time
        self._laps.append(lap_time)
        return lap_time

    def stop(self) -> float:
        """Остановка"""
        if self._start_time is None:
            return 0.0
        total = time.time() - self._start_time
        return total

    def get_laps(self) -> list:
        """Получение кругов"""
        return list(self._laps)

    def split(self) -> list:
        """Разбивка по кругам"""
        if not self._laps:
            return []
        laps = [self._laps[0]]
        for i in range(1, len(self._laps)):
            laps.append(self._laps[i] - self._laps[i-1])
        return laps


class RateTracker:
    """Трекер скорости"""

    def __init__(self, window: float = 60.0):
        self.window = window
        self._events: list = []

    def record(self):
        """Запись события"""
        now = time.time()
        self._events.append(now)
        # Clean old events
        self._events = [e for e in self._events if now - e < self.window]

    def rate(self) -> float:
        """Скорость (событий в секунду)"""
        if not self._events:
            return 0.0
        duration = self._events[-1] - self._events[0] if len(self._events) > 1 else 1.0
        return len(self._events) / duration

    def count(self) -> int:
        """Количество событий"""
        return len(self._events)


# Singleton
_timer: Timer = None


def get_timer(name: str = "default") -> Timer:
    """Получение таймера"""
    return Timer(name)
