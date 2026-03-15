"""
Circuit Breaker для AI провайдеров
Защита от каскадных отказов при недоступности провайдера.
"""

import time
import threading
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger("orchestration.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Конфигурация Circuit Breaker"""
    failure_threshold: int = 5          # Open after N failures
    success_threshold: int = 3          # Close after N successes (half-open)
    timeout: float = 30.0               # Seconds before trying half-open
    half_open_max_calls: int = 3        # Max parallel calls in half-open
    excluded_exceptions: tuple = ()     # Exceptions that don't count as failure


@dataclass
class CircuitBreakerMetrics:
    """Метрики Circuit Breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    last_failure_time: float = 0.0
    last_failure_reason: str = ""
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    """
    Circuit Breaker с состояниями CLOSED → OPEN → HALF_OPEN → CLOSED
    
    States:
    - CLOSED: нормальная работа, все вызовы проходят
    - OPEN: провайдер недоступен, вызовы отклоняются быстро
    - HALF_OPEN: тестирование восстановления, ограниченное число вызовов
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self._state = CircuitState.CLOSED
        self._lock = threading.RLock()
        self._metrics = CircuitBreakerMetrics()
        
        self._last_state_change = time.time()
        self._half_open_calls = 0
    
    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._check_state_transition()
            return self._state
    
    @property
    def is_available(self) -> bool:
        """Проверка доступности провайдера"""
        return self.state != CircuitState.OPEN
    
    @property
    def metrics(self) -> CircuitBreakerMetrics:
        return self._metrics
    
    def _check_state_transition(self):
        """Проверка перехода состояний по таймауту"""
        now = time.time()
        elapsed = now - self._last_state_change
        
        if self._state == CircuitState.OPEN:
            if elapsed >= self.config.timeout:
                logger.info(f"[{self.name}] Circuit OPEN → HALF_OPEN (timeout)")
                self._state = CircuitState.HALF_OPEN
                self._last_state_change = now
                self._half_open_calls = 0
                self._metrics.state_changes += 1
    
    def _can_execute(self) -> bool:
        """Проверка возможности выполнения вызова"""
        if self._state == CircuitState.CLOSED:
            return True
        
        if self._state == CircuitState.OPEN:
            return False
        
        # HALF_OPEN
        return self._half_open_calls < self.config.half_open_max_calls
    
    def record_success(self):
        """Запись успешного вызова"""
        with self._lock:
            self._metrics.successful_calls += 1
            self._metrics.total_calls += 1
            self._metrics.consecutive_failures = 0
            
            if self._state == CircuitState.HALF_OPEN:
                self._metrics.consecutive_successes += 1
                self._half_open_calls -= 1
                
                if self._metrics.consecutive_successes >= self.config.success_threshold:
                    logger.info(f"[{self.name}] Circuit HALF_OPEN → CLOSED")
                    self._state = CircuitState.CLOSED
                    self._last_state_change = time.time()
                    self._metrics.state_changes += 1
                    self._metrics.consecutive_successes = 0
            else:
                self._metrics.consecutive_successes = 1
    
    def record_failure(self, reason: str = ""):
        """Запись неудачного вызова"""
        with self._lock:
            self._metrics.failed_calls += 1
            self._metrics.total_calls += 1
            self._metrics.consecutive_failures += 1
            self._metrics.consecutive_successes = 0
            self._metrics.last_failure_time = time.time()
            self._metrics.last_failure_reason = reason[:100]
            
            if self._state == CircuitState.HALF_OPEN:
                logger.warning(f"[{self.name}] Circuit HALF_OPEN → OPEN (failure)")
                self._state = CircuitState.OPEN
                self._last_state_change = time.time()
                self._metrics.state_changes += 1
                self._half_open_calls = 0
            elif self._metrics.consecutive_failures >= self.config.failure_threshold:
                logger.warning(f"[{self.name}] Circuit CLOSED → OPEN ({self._metrics.consecutive_failures} failures)")
                self._state = CircuitState.OPEN
                self._last_state_change = time.time()
                self._metrics.state_changes += 1
    
    def record_rejection(self):
        """Запись отклонённого вызова (быстрый fail)"""
        with self._lock:
            self._metrics.rejected_calls += 1
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Выполнение функции с Circuit Breaker защитой
        
        Returns:
            Result from func or raises CircuitBreakerOpenError if OPEN
        """
        if not self._can_execute():
            self.record_rejection()
            raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")
        
        if self._state == CircuitState.HALF_OPEN:
            with self._lock:
                self._half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except self.config.excluded_exceptions as e:
            # Исключения не считаем за failure
            logger.debug(f"[{self.name}] Excluded exception: {e}")
            raise
        except Exception as e:
            self.record_failure(str(e))
            raise
    
    def get_status(self) -> dict:
        """Получение статуса Circuit Breaker"""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "available": self.is_available,
                "metrics": {
                    "total_calls": self._metrics.total_calls,
                    "successful": self._metrics.successful_calls,
                    "failed": self._metrics.failed_calls,
                    "rejected": self._metrics.rejected_calls,
                    "consecutive_failures": self._metrics.consecutive_failures,
                    "state_changes": self._metrics.state_changes,
                },
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "timeout": self.config.timeout,
                }
            }


class CircuitBreakerOpenError(Exception):
    """Исключение при отклонении вызова из-за OPEN Circuit"""
    pass


class CircuitBreakerManager:
    """Менеджер для управления множеством Circuit Breakers"""
    
    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
    
    def get_or_create(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Получить или создать Circuit Breaker"""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Получить Circuit Breaker по имени"""
        return self._breakers.get(name)
    
    def get_all_status(self) -> dict:
        """Статус всех Circuit Breakers"""
        return {
            name: breaker.get_status() 
            for name, breaker in self._breakers.items()
        }
    
    def reset_all(self):
        """Сброс всех Circuit Breakers"""
        with self._lock:
            for breaker in self._breakers.values():
                breaker._state = CircuitState.CLOSED
                breaker._metrics = CircuitBreakerMetrics()
                breaker._last_state_change = time.time()
            logger.info("All circuits reset to CLOSED")


# Глобальный экземпляр
_breakers = CircuitBreakerManager()


def get_breaker(name: str, **config_kwargs) -> CircuitBreaker:
    """Получить Circuit Breaker для провайдера"""
    config = CircuitBreakerConfig(**config_kwargs)
    return _breakers.get_or_create(name, config)


def circuit_breaker(name: str, **config_kwargs):
    """Декоратор для функций с Circuit Breaker"""
    def decorator(func: Callable) -> Callable:
        breaker = get_breaker(name, **config_kwargs)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.execute(func, *args, **kwargs)
        
        wrapper.breaker = breaker
        return wrapper
    return decorator
