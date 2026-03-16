"""Pipeline locks for concurrency control"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger("orchestration.locks")


class PipelineLock:
    """Pipeline lock"""
    
    def __init__(self, name: str):
        self.name = name
        self.lock = asyncio.Lock()
        self.holder: Optional[str] = None
    
    async def acquire(self, holder: str) -> bool:
        """Acquire lock"""
        if self.lock.locked():
            return False
        await self.lock.acquire()
        self.holder = holder
        return True
    
    async def release(self):
        """Release lock"""
        self.holder = None
        self.lock.release()


class LockManager:
    """Manage locks"""
    
    def __init__(self):
        self.locks = {}
    
    def get_lock(self, name: str) -> PipelineLock:
        if name not in self.locks:
            self.locks[name] = PipelineLock(name)
        return self.locks[name]
