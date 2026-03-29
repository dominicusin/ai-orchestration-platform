"""
Circuit breaker pattern implementation
Реализация паттерна Circuit Breaker
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger("orchestration.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Конфигурация circuit breaker"""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 30.0
    half_open_max_calls: int = 3


@dataclass
class CircuitBreakerStats:
    """Статистика circuit breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: float = None
    last_success_time: float = None


class CircuitBreaker:
    """
    Circuit Breaker для защиты от каскадных отказов
    """

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0
        self._stats = CircuitBreakerStats()

    @property
    def state(self) -> CircuitState:
        """Получение текущего состояния"""
        if self._state == CircuitState.OPEN:
            # Check if timeout has passed
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.timeout:
                    logger.info(f"Circuit {self.name}: transitioning to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
        return self._state

    def _can_execute(self) -> bool:
        """Проверка возможности выполнения"""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            return False
        elif state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.config.half_open_max_calls
        return False

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Выполнение функции с circuit breaker"""
        if not self._can_execute():
            self._stats.rejected_calls += 1
            raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")

        self._stats.total_calls += 1

        if self.state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._on_success()
            return result

        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        """Обработка успешного вызова"""
        self._stats.successful_calls += 1
        self._stats.last_success_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                logger.info(f"Circuit {self.name}: transitioning to CLOSED")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
        else:
            # Reset failure count on success in closed state
            self._failure_count = 0

    def _on_failure(self):
        """Обработка неудачного вызова"""
        self._stats.failed_calls += 1
        self._last_failure_time = time.time()
        self._stats.last_failure_time = self._last_failure_time
        self._failure_count += 1
        self._success_count = 0

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open goes back to open
            logger.info(f"Circuit {self.name}: transitioning to OPEN (half-open failure)")
            self._state = CircuitState.OPEN

        elif self._failure_count >= self.config.failure_threshold:
            logger.warning(f"Circuit {self.name}: transitioning to OPEN")
            self._state = CircuitState.OPEN

    def get_stats(self) -> CircuitBreakerStats:
        """Получение статистики"""
        self._stats.state = self.state
        return self._stats

    def reset(self):
        """Сброс circuit breaker"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0
        logger.info(f"Circuit {self.name}: manually reset")


class CircuitBreakerOpenError(Exception):
    """Исключение при открытом circuit breaker"""
    pass


class CircuitBreakerManager:
    """Менеджер circuit breakers"""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Получение или создание circuit breaker"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]

    def get_all_stats(self) -> dict:
        """Получение статистики всех breakers"""
        return {
            name: breaker.get_stats().__dict__
            for name, breaker in self._breakers.items()
        }


# Singleton
_breaker_manager: CircuitBreakerManager | None = None


def get_breaker_manager() -> CircuitBreakerManager:
    """Получение менеджера"""
    global _breaker_manager
    if _breaker_manager is None:
        _breaker_manager = CircuitBreakerManager()
    return _breaker_manager
