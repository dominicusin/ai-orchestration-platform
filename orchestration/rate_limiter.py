"""Rate limiter for API calls"""

import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger("orchestration.rate_limiter")


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10


class TokenBucket:
    """Token bucket algorithm"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens"""
        now = time.time()
        elapsed = now - self.last_update
        
        # Refill tokens
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def wait_time(self, tokens: int = 1) -> float:
        """Get wait time needed"""
        if self.tokens >= tokens:
            return 0
        
        needed = tokens - self.tokens
        return needed / self.rate


class RateLimiter:
    """Multi-level rate limiter"""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        
        # Per-minute bucket
        self.minute_bucket = TokenBucket(
            rate=self.config.requests_per_minute / 60,
            capacity=self.config.requests_per_minute,
        )
        
        # Per-hour bucket
        self.hour_bucket = TokenBucket(
            rate=self.config.requests_per_hour / 3600,
            capacity=self.config.requests_per_hour,
        )
        
        # Per-day bucket
        self.day_bucket = TokenBucket(
            rate=self.config.requests_per_day / 86400,
            capacity=self.config.requests_per_day,
        )
        
        # Provider-specific limiters
        self.provider_limiters: Dict[str, TokenBucket] = {}
        
        # Request tracking
        self.requests: Dict[str, list] = defaultdict(list)
    
    def check_limit(self, key: str = "default") -> tuple:
        """Check if request is allowed"""
        # Check all levels
        if not self.minute_bucket.consume():
            return False, "minute_limit"
        
        if not self.hour_bucket.consume():
            return False, "hour_limit"
        
        if not self.day_bucket.consume():
            return False, "day_limit"
        
        # Track request
        self.requests[key].append(time.time())
        
        return True, "ok"
    
    def check_provider_limit(self, provider: str, limit: int) -> bool:
        """Check provider-specific limit"""
        if provider not in self.provider_limiters:
            self.provider_limiters[provider] = TokenBucket(
                rate=limit / 60,
                capacity=limit,
            )
        
        return self.provider_limiters[provider].consume()
    
    def get_status(self) -> Dict:
        """Get rate limiter status"""
        return {
            "minute": {
                "tokens": self.minute_bucket.tokens,
                "capacity": self.minute_bucket.capacity,
            },
            "hour": {
                "tokens": self.hour_bucket.tokens,
                "capacity": self.hour_bucket.capacity,
            },
            "day": {
                "tokens": self.day_bucket.tokens,
                "capacity": self.day_bucket.capacity,
            },
        }


# Global limiter
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
