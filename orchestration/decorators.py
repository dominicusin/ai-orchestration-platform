"""
Decorators for common functionality
Декораторы для часто используемой функциональности
"""

import asyncio
import functools
import logging
import time
from collections.abc import Callable

logger = logging.getLogger("orchestration.decorators")


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Декоратор повтора при ошибке"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception

        return wrapper
    return decorator


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Асинхронный декоратор повтора"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception

        return wrapper
    return decorator


def timing(func: Callable) -> Callable:
    """Декоратор замера времени выполнения"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.debug(f"{func.__name__} took {duration:.4f}s")
        return result
    return wrapper


def async_timing(func: Callable) -> Callable:
    """Асинхронный декоратор замера времени"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.debug(f"{func.__name__} took {duration:.4f}s")
        return result
    return wrapper


def cache(ttl: float = 300.0):
    """Декоратор кэширования"""
    def decorator(func):
        cache_data = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()

            if key in cache_data:
                value, timestamp = cache_data[key]
                if now - timestamp < ttl:
                    return value

            result = func(*args, **kwargs)
            cache_data[key] = (result, now)
            return result

        return wrapper
    return decorator


def log_calls(logger_instance: logging.Logger = None):
    """Декоратор логирования вызовов"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger_instance or logger
            log.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                log.debug(f"{func.__name__} returned {result}")
                return result
            except Exception as e:
                log.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        return wrapper
    return decorator


def deprecated(message: str = "This function is deprecated"):
    """Декоратор устаревшей функции"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.warning(f"{func.__name__} is deprecated: {message}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def once(func: Callable) -> Callable:
    """Декоратор однократного выполнения"""
    result = None
    executed = False

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal result, executed
        if not executed:
            result = func(*args, **kwargs)
            executed = True
        return result

    return wrapper


def rate_limit(calls: int, period: float = 60.0):
    """Декоратор ограничения частоты вызовов"""
    def decorator(func):
        call_times = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            call_times[:] = [t for t in call_times if now - t < period]

            if len(call_times) >= calls:
                sleep_time = period - (now - call_times[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)

            call_times.append(time.time())
            return func(*args, **kwargs)

        return wrapper
    return decorator


def validate_args(**validators):
    """Декоратор валидации аргументов"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for arg_name, validator in validators.items():
                if arg_name in kwargs:
                    value = kwargs[arg_name]
                    if not validator(value):
                        raise ValueError(f"Invalid argument {arg_name}={value}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def memoize(func: Callable) -> Callable:
    """Декоратор мемоизации"""
    cache = {}

    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    return wrapper


def synchronized(lock: asyncio.Lock = None):
    """Декоратор синхронизации для async функций"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with lock or asyncio.Lock():
                return await func(*args, **kwargs)
        return wrapper
    return decorator
