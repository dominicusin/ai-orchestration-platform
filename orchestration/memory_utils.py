"""
Memory optimization utilities
Утилиты для оптимизации памяти
"""

import gc
import logging
import sys
import weakref
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("orchestration.memory")


@dataclass
class MemorySnapshot:
    """Снепшот памяти"""
    timestamp: str
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    objects: int
    gc_counts: tuple = field(default_factory=lambda: (0, 0, 0, 0))


@dataclass
class MemoryStats:
    """Статистика памяти"""
    initial_mb: float = 0.0
    current_mb: float = 0.0
    peak_mb: float = 0.0
    allocations: int = 0
    deallocations: int = 0
    gc_runs: int = 0

    @property
    def delta_mb(self) -> float:
        return self.current_mb - self.initial_mb

    @property
    def delta_percent(self) -> float:
        if self.initial_mb == 0:
            return 0.0
        return (self.delta_mb / self.initial_mb) * 100


class MemoryTracker:
    """
    Трекер использования памяти
    """

    def __init__(self, enable_gc_tracking: bool = True):
        self.enable_gc_tracking = enable_gc_tracking
        self._enabled = False
        self._snapshots: list[MemorySnapshot] = []
        self.stats = MemoryStats()
        self._callbacks: list[Callable] = []
        self._tracked_objects: list[weakref.ref] = []

    def start(self):
        """Запуск трекера"""
        self._enabled = True
        self.stats.initial_mb = self.get_current_memory()
        self.stats.peak_mb = self.stats.initial_mb
        logger.info(f"Memory tracker started: {self.stats.initial_mb:.1f} MB")

    def stop(self):
        """Остановка трекера"""
        self._enabled = False
        self.stats.current_mb = self.get_current_memory()
        logger.info(f"Memory tracker stopped: {self.stats.current_mb:.1f} MB")

    def get_current_memory(self) -> float:
        """Получение текущего использования памяти в MB"""
        try:
            import resource
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # Linux returns KB, macOS returns bytes
            if sys.platform == "darwin":
                return rss / 1024 / 1024  # Convert to MB
            return rss / 1024  # Convert to MB
        except Exception:
            pass

        # Fallback: estimate from gc objects
        return len(gc.get_objects()) * 0.0001

    def take_snapshot(self) -> MemorySnapshot:
        """Создание снепшота памяти"""
        snapshot = MemorySnapshot(
            timestamp=datetime.now().isoformat(),
            rss_mb=self.get_current_memory(),
            vms_mb=0.0,
            objects=len(gc.get_objects()),
            gc_counts=gc.get_count() if self.enable_gc_tracking else (0, 0, 0, 0),
        )

        if self._enabled:
            self._snapshots.append(snapshot)
            self.stats.current_mb = snapshot.rss_mb
            if snapshot.rss_mb > self.stats.peak_mb:
                self.stats.peak_mb = snapshot.rss_mb

            # Check threshold and trigger callbacks
            for callback in self._callbacks:
                try:
                    callback(snapshot)
                except Exception as e:
                    logger.warning(f"Memory callback error: {e}")

        return snapshot

    def track_object(self, obj: Any):
        """Отслеживание объекта"""
        ref = weakref.ref(obj, self._on_object_collected)
        self._tracked_objects.append(ref)

    def _on_object_collected(self, ref):
        """Callback при сборке объекта"""
        self.stats.deallocations += 1

    def register_callback(self, callback: Callable[[MemorySnapshot], None]):
        """Регистрация callback при превышении порога"""
        self._callbacks.append(callback)

    def get_snapshots(self) -> list[MemorySnapshot]:
        """Получение всех снепшотов"""
        return self._snapshots

    def get_stats(self) -> dict:
        """Получение статистики"""
        return {
            "initial_mb": f"{self.stats.initial_mb:.1f}",
            "current_mb": f"{self.stats.current_mb:.1f}",
            "peak_mb": f"{self.stats.peak_mb:.1f}",
            "delta_mb": f"{self.stats.delta_mb:.1f}",
            "delta_percent": f"{self.stats.delta_percent:.1f}%",
            "tracked_objects": len(self._tracked_objects),
            "snapshots": len(self._snapshots),
        }

    def force_gc(self):
        """Принудительная сборка мусора"""
        before = self.get_current_memory()
        gc.collect()
        after = self.get_current_memory()
        self.stats.gc_runs += 1
        logger.info(f"GC: {before:.1f} MB -> {after:.1f} MB (freed {before - after:.1f} MB)")

    def clear_snapshots(self):
        """Очистка снепшотов"""
        self._snapshots.clear()

    def clear_tracked_objects(self):
        """Очистка отслеживаемых объектов"""
        self._tracked_objects.clear()


class MemoryOptimizer:
    """
    Оптимизатор памяти
    """

    def __init__(self, threshold_mb: float = 100.0):
        self.threshold_mb = threshold_mb
        self.tracker = MemoryTracker()
        self._auto_gc_enabled = False

    def start_auto_gc(self, check_interval: float = 60.0):
        """Автоматическая сборка мусора"""
        self._auto_gc_enabled = True
        self.tracker.start()

        # Register callback
        def check_threshold(snapshot: MemorySnapshot):
            if snapshot.rss_mb > self.threshold_mb:
                logger.warning(f"Memory threshold exceeded: {snapshot.rss_mb:.1f} MB")
                self.tracker.force_gc()

        self.tracker.register_callback(check_threshold)

    def stop_auto_gc(self):
        """Остановка автоматической GC"""
        self._auto_gc_enabled = False

    def optimize_dataclass(self, obj: Any) -> Any:
        """Оптимизация dataclass"""
        if hasattr(obj, "__dataclass_fields__"):
            # Convert to tuple for memory efficiency
            fields = []
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name, None)
                if isinstance(value, list):
                    # Convert lists to tuples
                    value = tuple(value)
                fields.append(value)
            return tuple(fields)
        return obj

    def clear_circular_refs(self, obj: Any):
        """Очистка циклических ссылок"""
        if hasattr(obj, "__dict__"):
            for key in list(obj.__dict__.keys()):
                value = obj.__dict__[key]
                if isinstance(value, (dict, list)):
                    # Clear large collections
                    if len(value) > 1000:
                        obj.__dict__[key] = None

    def estimate_size(self, obj: Any) -> int:
        """Оценка размера объекта в байтах"""
        try:
            import sys
            return sys.getsizeof(obj)
        except Exception:
            return 0


# Singleton
_memory_tracker: MemoryTracker | None = None


def get_memory_tracker() -> MemoryTracker:
    """Получение трекера памяти"""
    global _memory_tracker
    if _memory_tracker is None:
        _memory_tracker = MemoryTracker()
    return _memory_tracker


def get_memory_optimizer(threshold_mb: float = 100.0) -> MemoryOptimizer:
    """Получение оптимизатора памяти"""
    return MemoryOptimizer(threshold_mb)
