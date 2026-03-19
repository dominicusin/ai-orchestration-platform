"""Rate limiter for API calls"""

import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger("orchestration.rate_limiter")


@dataclass
class RateLimit:
    """Rate limit config"""
    calls: int
    period: float  # seconds


class TokenBucket:
    """Token bucket algorithm"""
    
    def __init__(self, rate: int, period: float = 1.0):
        self.rate = rate
        self.period = period
        self.tokens = rate
        self.last_update = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        
        # Refill tokens
        self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.period))
        self.last_update = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def wait_time(self) -> float:
        if self.tokens >= 1:
            return 0
        return (1 - self.tokens) * (self.period / self.rate)


class RateLimiter:
    """Rate limiter"""
    
    def __init__(self):
        self.limiters: Dict[str, TokenBucket] = {}
    
    def add_limit(self, name: str, calls: int, period: float = 1.0):
        self.limiters[name] = TokenBucket(calls, period)
    
    def try_acquire(self, name: str, tokens: int = 1) -> bool:
        if name not in self.limiters:
            return True
        return self.limiters[name].consume(tokens)
    
    def wait_until(self, name: str):
        if name in self.limiters:
            wait = self.limiters[name].wait_time()
            if wait > 0:
                time.sleep(wait)


_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter