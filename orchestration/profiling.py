"""
Profiling utilities
Утилиты для профилирования производительности
"""

import cProfile
import functools
import logging
import pstats
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from io import StringIO

logger = logging.getLogger("orchestration.profiling")


@dataclass
class ProfileResult:
    """Результат профилирования"""
    function_name: str
    calls: int
    total_time: float
    per_call: float
    cum_time: float
    per_call_cum: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TimingResult:
    """Результат замера времени"""
    name: str
    start_time: float
    end_time: float
    duration: float
    metadata: dict = field(default_factory=dict)


class Profiler:
    """
    Профилировщик с поддержкой:
    - Function profiling
    - Line-by-line profiling
    - Memory profiling
    - Timing context manager
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._profiler: cProfile.Profile | None = None
        self._results: list[ProfileResult] = []
        self._timings: list[TimingResult] = []

    def profile(self, func: Callable) -> Callable:
        """Декоратор для профилирования функции"""
        if not self.enabled:
            return func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                profiler.disable()
                self._process_profiler_result(profiler, func.__name__)

        return wrapper

    def _process_profiler_result(self, profiler: cProfile.Profile, func_name: str):
        """Обработка результатов профилирования"""
        stats = pstats.Stats(profiler)
        stats.strip_dirs()
        stats.sort_stats("cumulative")

        # Get top function stats
        stream = StringIO()
        stats.stream = stream
        stats.print_stats(1)

        # Parse first function result
        lines = stream.getvalue().split("\n")
        for line in lines:
            if "function calls" in line:
                # Extract timing info
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        total_time = float(parts[3].strip("()"))
                        calls = int(parts[0])

                        result = ProfileResult(
                            function_name=func_name,
                            calls=calls,
                            total_time=total_time,
                            per_call=total_time / calls if calls > 0 else 0,
                            cum_time=total_time,
                            per_call_cum=total_time / calls if calls > 0 else 0,
                        )
                        self._results.append(result)
                    except (ValueError, IndexError):
                        pass

    def get_results(self) -> list[ProfileResult]:
        """Получение результатов"""
        return self._results

    def clear_results(self):
        """Очистка результатов"""
        self._results.clear()

    def get_summary(self) -> str:
        """Получение сводки"""
        if not self._results:
            return "No profiling results"

        lines = ["=== Profiling Summary ==="]
        for r in self._results:
            lines.append(
                f"{r.function_name}: {r.total_time:.4f}s "
                f"({r.calls} calls, {r.per_call*1000:.3f}ms per call)"
            )
        return "\n".join(lines)


class Timer:
    """
    Контекстный менеджер для замера времени
    """

    def __init__(self, name: str, metadata: dict = None):
        self.name = name
        self.metadata = metadata or {}
        self.start_time: float = 0
        self.end_time: float = 0
        self.result: TimingResult | None = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        self.result = TimingResult(
            name=self.name,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=duration,
            metadata=self.metadata,
        )
        return False

    def get_duration(self) -> float:
        """Получение длительности"""
        return self.result.duration if self.result else 0


def timeit(func: Callable = None, *, name: str = None):
    """Декоратор для замера времени выполнения"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return f(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                func_name = name or f.__name__
                logger.debug(f"{func_name} took {duration:.4f}s")

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


class PerformanceMonitor:
    """
    Монитор производительности
    """

    def __init__(self):
        self._timings: dict[str, list[float]] = {}
        self._call_counts: dict[str, int] = {}

    def record(self, name: str, duration: float):
        """Запись времени выполнения"""
        if name not in self._timings:
            self._timings[name] = []
            self._call_counts[name] = 0

        self._timings[name].append(duration)
        self._call_counts[name] += 1

    def get_stats(self, name: str) -> dict:
        """Получение статистики по функции"""
        if name not in self._timings:
            return {}

        timings = self._timings[name]
        return {
            "calls": self._call_counts[name],
            "total": sum(timings),
            "avg": sum(timings) / len(timings),
            "min": min(timings),
            "max": max(timings),
        }

    def get_all_stats(self) -> dict:
        """Получение всей статистики"""
        return {name: self.get_stats(name) for name in self._timings}

    def clear(self):
        """Очистка"""
        self._timings.clear()
        self._call_counts.clear()


# Decorator for async functions
def async_timeit(func: Callable = None, *, name: str = None):
    """Декоратор для замера времени async функций"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await f(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                func_name = name or f.__name__
                logger.debug(f"{func_name} took {duration:.4f}s")

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


# Singleton
_profiler: Profiler | None = None
_perf_monitor: PerformanceMonitor | None = None


def get_profiler(enabled: bool = True) -> Profiler:
    """Получение профилировщика"""
    global _profiler
    if _profiler is None:
        _profiler = Profiler(enabled)
    return _profiler


def get_performance_monitor() -> PerformanceMonitor:
    """Получение монитора производительности"""
    global _perf_monitor
    if _perf_monitor is None:
        _perf_monitor = PerformanceMonitor()
    return _perf_monitor
