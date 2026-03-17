"""Retry strategies for distributed tasks"""

import asyncio
import logging
import time
from typing import Callable, Any, Optional, Type
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("orchestration.retry")


class RetryStrategy(str, Enum):
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0
    jitter: bool = True


class RetryPolicy:
    """Retry policy with various strategies"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.attempt = 0
    
    def get_delay(self) -> float:
        """Calculate delay based on strategy"""
        delay = self.config.initial_delay
        
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.initial_delay
        
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.initial_delay * (self.attempt + 1)
        
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (self.config.backoff_multiplier ** self.attempt)
        
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            delay = self.config.initial_delay * self._fibonacci(self.attempt + 1)
        
        # Apply jitter
        if self.config.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return min(delay, self.config.max_delay)
    
    def _fibonacci(self, n: int) -> int:
        """Fibonacci number"""
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b
    
    def should_retry(self) -> bool:
        """Check if should retry"""
        return self.attempt < self.config.max_attempts
    
    def reset(self):
        """Reset attempt counter"""
        self.attempt = 0


def with_retry(
    func: Callable,
    config: RetryConfig = None,
    retry_on: tuple = (Exception,),
) -> Callable:
    """Decorator to add retry logic"""
    
    async def async_wrapper(*args, **kwargs):
        policy = RetryPolicy(config)
        
        while policy.should_retry():
            try:
                return await func(*args, **kwargs)
            except retry_on as e:
                policy.attempt += 1
                if policy.should_retry():
                    delay = policy.get_delay()
                    logger.warning(f"Retry {policy.attempt}/{policy.config.max_attempts} after {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    raise
    
    def sync_wrapper(*args, **kwargs):
        policy = RetryPolicy(config)
        
        while policy.should_retry():
            try:
                return func(*args, **kwargs)
            except retry_on as e:
                policy.attempt += 1
                if policy.should_retry():
                    delay = policy.get_delay()
                    logger.warning(f"Retry {policy.attempt}/{policy.config.max_attempts} after {delay:.2f}s: {e}")
                    time.sleep(delay)
                else:
                    raise
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


class CircuitBreaker:
    """Circuit breaker pattern"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker"""
        
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Call async function with circuit breaker"""
        
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            raise
    
    def reset(self):
        """Reset circuit breaker"""
        self.failure_count = 0
        self.state = "closed"