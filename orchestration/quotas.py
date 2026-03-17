"""Pipeline quotas"""

import time
import logging
from typing import Dict, Optional

logger = logging.getLogger("orchestration.quotas")


class Quota:
    """Resource quota"""
    
    def __init__(self, limit: int, window: int = 60):
        self.limit = limit
        self.window = window
        self.used = 0
        self.reset_time = time.time() + window
    
    def consume(self, amount: int = 1) -> bool:
        now = time.time()
        
        if now > self.reset_time:
            self.used = 0
            self.reset_time = now + self.window
        
        if self.used + amount > self.limit:
            return False
        
        self.used += amount
        return True
    
    def remaining(self) -> int:
        return max(0, self.limit - self.used)


class QuotaManager:
    """Manage quotas"""
    
    def __init__(self):
        self.quotas: Dict[str, Quota] = {}
    
    def create(self, name: str, limit: int, window: int = 60):
        self.quotas[name] = Quota(limit, window)
    
    def check(self, name: str, amount: int = 1) -> bool:
        if name not in self.quotas:
            return True
        return self.quotas[name].consume(amount)
    
    def get_remaining(self, name: str) -> int:
        if name not in self.quotas:
            return -1
        return self.quotas[name].remaining()
