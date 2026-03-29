"""
Health check system
Система проверки здоровья сервисов
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("orchestration.health")


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Результат проверки"""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)


@dataclass
class HealthReport:
    """Общий отчёт о здоровье"""
    overall_status: HealthStatus
    checks: list[HealthCheckResult]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: float = 0.0


class HealthCheck:
    """Базовая проверка здоровья"""

    def __init__(
        self,
        name: str,
        check_func: Callable,
        timeout: float = 5.0,
        critical: bool = True,
    ):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.critical = critical

    async def execute(self) -> HealthCheckResult:
        """Выполнение проверки"""
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(self.check_func):
                result = await asyncio.wait_for(
                    self.check_func(),
                    timeout=self.timeout
                )
            else:
                result = self.check_func()

            latency = (time.time() - start_time) * 1000

            # Determine status based on result
            if result is True:
                status = HealthStatus.HEALTHY
            elif result is False:
                status = HealthStatus.UNHEALTHY
            elif isinstance(result, dict):
                status = HealthStatus(result.get("status", "healthy"))
                result_message = result.get("message", "")
            else:
                status = HealthStatus.HEALTHY

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=result_message if isinstance(result, dict) else "",
                latency_ms=latency,
            )

        except TimeoutError:
            latency = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Timeout after {self.timeout}s",
                latency_ms=latency,
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=latency,
            )


class HealthCheckManager:
    """
    Менеджер проверок здоровья
    """

    def __init__(self):
        self._checks: list[HealthCheck] = []
        self._last_report: HealthReport | None = None

    def register(
        self,
        name: str,
        check_func: Callable,
        timeout: float = 5.0,
        critical: bool = True,
    ):
        """Регистрация проверки"""
        check = HealthCheck(name, check_func, timeout, critical)
        self._checks.append(check)
        logger.info(f"Registered health check: {name}")

    async def check_all(self) -> HealthReport:
        """Проверка всех сервисов"""
        start_time = time.time()
        results = []

        # Run all checks in parallel
        tasks = [check.execute() for check in self._checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        check_results = []
        has_unhealthy = False

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                check_results.append(HealthCheckResult(
                    name=self._checks[i].name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(result),
                ))
                has_unhealthy = True
            else:
                check_results.append(result)
                if result.status == HealthStatus.UNHEALTHY:
                    if self._checks[i].critical:
                        has_unhealthy = True

        # Determine overall status
        if has_unhealthy:
            overall = HealthStatus.UNHEALTHY
        elif any(r.status == HealthStatus.DEGRADED for r in check_results):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        duration = (time.time() - start_time) * 1000

        report = HealthReport(
            overall_status=overall,
            checks=check_results,
            duration_ms=duration,
        )

        self._last_report = report
        return report

    def get_last_report(self) -> HealthReport | None:
        """Получение последнего отчёта"""
        return self._last_report

    def get_status_summary(self) -> dict:
        """Получение краткой сводки"""
        if not self._last_report:
            return {"status": "unknown"}

        return {
            "status": self._last_report.overall_status.value,
            "checks": {
                c.name: c.status.value for c in self._last_report.checks
            },
            "duration_ms": self._last_report.duration_ms,
        }


# Built-in health checks

async def check_redis_health(redis_client) -> bool:
    """Проверка Redis"""
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False


async def check_database_health(db_connection) -> bool:
    """Проверка базы данных"""
    try:
        # Simple query
        result = db_connection.execute("SELECT 1")
        return result is not None
    except Exception:
        return False


async def check_disk_space(path: str = "/", threshold_percent: float = 90.0) -> dict:
    """Проверка дискового пространства"""
    import shutil
    try:
        usage = shutil.disk_usage(path)
        percent = (usage.used / usage.total) * 100

        return {
            "status": "healthy" if percent < threshold_percent else "unhealthy",
            "percent": percent,
            "free_gb": usage.free / (1024**3),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_memory_usage(threshold_percent: float = 90.0) -> dict:
    """Проверка использования памяти"""
    import psutil
    try:
        memory = psutil.virtual_memory()
        percent = memory.percent

        return {
            "status": "healthy" if percent < threshold_percent else "unhealthy",
            "percent": percent,
            "available_mb": memory.available / (1024**2),
        }
    except Exception:
        return {"status": "healthy"}  # psutil may not be available


async def check_api_endpoint(url: str, timeout: float = 5.0) -> bool:
    """Проверка API эндпоинта"""
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                return resp.status < 500
    except Exception:
        return False


# Singleton
_health_manager: HealthCheckManager | None = None


def get_health_manager() -> HealthCheckManager:
    """Получение менеджера здоровья"""
    global _health_manager
    if _health_manager is None:
        _health_manager = HealthCheckManager()
    return _health_manager
