"""
Resource managers
Менеджеры ресурсов (CPU, memory, disk)
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime

import psutil

logger = logging.getLogger("orchestration.resource_managers")


@dataclass
class ResourceUsage:
    """Использование ресурсов"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_used_gb: float
    disk_free_gb: float
    disk_percent: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ResourceLimit:
    """Лимит ресурсов"""
    max_memory_percent: float = 90.0
    max_disk_percent: float = 90.0
    max_cpu_percent: float = 95.0


class ResourceMonitor:
    """
    Мониторинг ресурсов системы
    """

    def __init__(self):
        self._limits = ResourceLimit()

    def set_limits(self, limits: ResourceLimit):
        """Установка лимитов"""
        self._limits = limits

    def get_usage(self) -> ResourceUsage:
        """Получение текущего использования"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return ResourceUsage(
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_used_gb=disk.used / (1024 * 1024 * 1024),
            disk_free_gb=disk.free / (1024 * 1024 * 1024),
            disk_percent=disk.percent,
        )

    def check_limits(self) -> dict:
        """Проверка лимитов"""
        usage = self.get_usage()
        warnings = []

        if usage.memory_percent > self._limits.max_memory_percent:
            warnings.append(f"Memory critical: {usage.memory_percent:.1f}%")

        if usage.disk_percent > self._limits.max_disk_percent:
            warnings.append(f"Disk critical: {usage.disk_percent:.1f}%")

        if usage.cpu_percent > self._limits.max_cpu_percent:
            warnings.append(f"CPU critical: {usage.cpu_percent:.1f}%")

        return {
            "usage": usage,
            "warnings": warnings,
            "within_limits": len(warnings) == 0,
        }

    def get_process_info(self, pid: int = None) -> dict:
        """Информация о процессе"""
        pid = pid or os.getpid()
        try:
            process = psutil.Process(pid)
            with process.oneshot():
                return {
                    "pid": pid,
                    "name": process.name(),
                    "cpu_percent": process.cpu_percent(),
                    "memory_mb": process.memory_info().rss / (1024 * 1024),
                    "num_threads": process.num_threads(),
                    "status": process.status(),
                }
        except psutil.NoSuchProcess:
            return {"error": "Process not found"}


class MemoryManager:
    """
    Менеджер памяти
    """

    def __init__(self, threshold_percent: float = 85.0):
        self.threshold_percent = threshold_percent

    def is_memory_available(self, required_mb: float = 100) -> bool:
        """Проверка доступной памяти"""
        memory = psutil.virtual_memory()
        available_mb = memory.available / (1024 * 1024)
        return available_mb >= required_mb

    def get_memory_info(self) -> dict:
        """Информация о памяти"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "total_mb": memory.total / (1024 * 1024),
            "available_mb": memory.available / (1024 * 1024),
            "used_mb": memory.used / (1024 * 1024),
            "percent": memory.percent,
            "swap_total_mb": swap.total / (1024 * 1024),
            "swap_used_mb": swap.used / (1024 * 1024),
            "swap_percent": swap.percent,
        }

    def is_critical(self) -> bool:
        """Критический уровень памяти"""
        return psutil.virtual_memory().percent >= self.threshold_percent


class DiskManager:
    """
    Менеджер диска
    """

    def __init__(self, path: str = "/", threshold_percent: float = 90.0):
        self.path = path
        self.threshold_percent = threshold_percent

    def get_disk_info(self) -> dict:
        """Информация о диске"""
        usage = psutil.disk_usage(self.path)

        return {
            "path": self.path,
            "total_gb": usage.total / (1024 * 1024 * 1024),
            "used_gb": usage.used / (1024 * 1024 * 1024),
            "free_gb": usage.free / (1024 * 1024 * 1024),
            "percent": usage.percent,
        }

    def is_critical(self) -> bool:
        """Критический уровень диска"""
        return psutil.disk_usage(self.path).percent >= self.threshold_percent


class CPUMonitor:
    """
    Монитор CPU
    """

    def __init__(self, threshold_percent: float = 95.0):
        self.threshold_percent = threshold_percent

    def get_cpu_info(self) -> dict:
        """Информация о CPU"""
        cpu_times = psutil.cpu_times()

        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "percent": psutil.cpu_percent(interval=0.1, percpu=False),
            "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True),
            "user_percent": cpu_times.user / (cpu_times.user + cpu_times.system) * 100 if (cpu_times.user + cpu_times.system) > 0 else 0,
        }

    def is_critical(self) -> bool:
        """Критическая нагрузка CPU"""
        return psutil.cpu_percent(interval=0.1) >= self.threshold_percent


# Singleton
_resource_monitor: ResourceMonitor | None = None


def get_resource_monitor() -> ResourceMonitor:
    """Получение монитора ресурсов"""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor
