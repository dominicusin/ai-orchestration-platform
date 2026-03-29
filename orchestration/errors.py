"""
Error handling and custom exceptions
Обработка ошибок и пользовательские исключения
"""

import logging
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("orchestration.errors")


class OrchestrationError(Exception):
    """Base exception for orchestration"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PipelineError(OrchestrationError):
    """Pipeline execution error"""
    pass


class StageError(OrchestrationError):
    """Stage execution error"""
    def __init__(self, message: str, stage_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.stage_name = stage_name


class ValidationError(OrchestrationError):
    """Validation error"""
    pass


class ConfigurationError(OrchestrationError):
    """Configuration error"""
    pass


class ResourceError(OrchestrationError):
    """Resource allocation error"""
    pass


class TimeoutError(OrchestrationError):
    """Operation timeout error"""
    pass


class RetryExhaustedError(OrchestrationError):
    """Retry limit exceeded"""
    def __init__(self, message: str, attempts: int = 0, last_error: Exception = None, **kwargs):
        super().__init__(message, **kwargs)
        self.attempts = attempts
        self.last_error = last_error


class CircuitBreakerError(OrchestrationError):
    """Circuit breaker open error"""
    pass


class RateLimitError(OrchestrationError):
    """Rate limit exceeded error"""
    def __init__(self, message: str, retry_after: float = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


@dataclass
class ErrorContext:
    """Контекст ошибки"""
    error_type: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    traceback: str = ""
    context: dict = field(default_factory=dict)
    stack_trace: list[str] = field(default_factory=list)


class ErrorHandler:
    """Обработчик ошибок"""

    def __init__(self):
        self._handlers: dict[type, Callable] = {}
        self._error_log: list[ErrorContext] = []
        self._max_log_size = 1000

    def register_handler(self, error_type: type, handler: Callable):
        """Регистрация обработчика для типа ошибки"""
        self._handlers[error_type] = handler

    def handle(self, error: Exception, context: dict = None, reraise: bool = False) -> Any:
        """Обработка ошибки"""
        # Log the error
        self._log_error(error, context)

        # Find handler
        handler = self._handlers.get(type(error))
        if handler:
            return handler(error, context)

        # Default handling
        if reraise:
            return self._default_handler(error, context)
        return None

    def _log_error(self, error: Exception, context: dict = None):
        """Логирование ошибки"""
        error_ctx = ErrorContext(
            error_type=type(error).__name__,
            message=str(error),
            traceback=traceback.format_exc(),
            context=context or {},
            stack_trace=traceback.format_stack(),
        )
        self._error_log.append(error_ctx)

        # Trim log
        if len(self._error_log) > self._max_log_size:
            self._error_log = self._error_log[-self._max_log_size:]

    def _default_handler(self, error: Exception, context: dict = None) -> Any:
        """Обработчик по умолчанию"""
        logger.error(f"Error: {error}", exc_info=True)
        raise error

    def get_error_log(self) -> list[ErrorContext]:
        """Получение лога ошибок"""
        return list(self._error_log)

    def get_errors_by_type(self, error_type: str) -> list[ErrorContext]:
        """Получение ошибок по типу"""
        return [e for e in self._error_log if e.error_type == error_type]

    def clear_log(self):
        """Очистка лога"""
        self._error_log.clear()


class ErrorRecovery:
    """Восстановление после ошибок"""

    @staticmethod
    def with_fallback(fallback: Callable, primary: Callable, *args, **kwargs):
        """Выполнение с fallback"""
        try:
            return primary(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary failed: {e}, using fallback")
            return fallback(*args, **kwargs)

    @staticmethod
    def with_retry(func: Callable, max_attempts: int = 3, delay: float = 1.0):
        """Выполнение с повтором"""
        last_error = None
        for attempt in range(max_attempts):
            try:
                return func()
            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(delay)
        raise last_error

    @staticmethod
    def with_circuit_breaker(breaker, func: Callable, *args, **kwargs):
        """Выполнение с circuit breaker"""
        if breaker.is_open():
            raise CircuitBreakerError("Circuit breaker is open")
        try:
            result = func(*args, **kwargs)
            breaker.record_success()
            return result
        except Exception:
            breaker.record_failure()
            raise


def safe_execute(func: Callable, default: Any = None, *args, **kwargs) -> Any:
    """Безопасное выполнение функции"""
    try:
        return func(*args, **kwargs)
    except Exception:
        return default


def async_safe_execute(func: Callable, default: Any = None):
    """Безопасное выполнение async функции"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            return default
    return wrapper


# Singleton
_error_handler: ErrorHandler | None = None


def get_error_handler() -> ErrorHandler:
    """Получение обработчика ошибок"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler
