"""Retry strategies for failed operations"""

import time
import asyncio
import logging
from typing import Callable, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("orchestration.retry")


class BackoffStrategy(Enum):
    """Backoff strategy"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    multiplier: float = 2.0
    jitter: bool = True


class RetryError(Exception):
    """Retry exhausted error"""
    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Failed after {attempts} attempts: {last_error}")


class Retry:
    """Retry decorator with backoff"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for attempt"""
        if self.config.backoff == BackoffStrategy.LINEAR:
            delay = self.config.initial_delay * attempt
        
        elif self.config.backoff == BackoffStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (self.config.multiplier ** (attempt - 1))
        
        elif self.config.backoff == BackoffStrategy.FIBONACCI:
            # Fibonacci: 1, 1, 2, 3, 5, 8...
            fib = [1, 1]
            for i in range(2, attempt + 1):
                fib.append(fib[i-1] + fib[i-2])
            delay = self.config.initial_delay * fib[min(attempt, len(fib)-1)]
        
        else:
            delay = self.config.initial_delay
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter
        if self.config.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute with retry"""
        last_error = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                last_error = e
                
                if attempt >= self.config.max_attempts:
                    logger.error(f"Retry exhausted after {attempt} attempts")
                    raise RetryError(attempt, e)
                
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
        
        raise RetryError(self.config.max_attempts, last_error)
    
    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async with retry"""
        last_error = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            
            except Exception as e:
                last_error = e
                
                if attempt >= self.config.max_attempts:
                    raise RetryError(attempt, e)
                
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        raise RetryError(self.config.max_attempts, last_error)


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
):
    """Decorator for retry"""
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        backoff=backoff,
    )
    
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            retry_obj = Retry(config)
            return await retry_obj.execute_async(func, *args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            retry_obj = Retry(config)
            return retry_obj.execute(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
