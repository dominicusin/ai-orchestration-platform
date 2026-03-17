"""Pipeline resource managers"""

import logging
from typing import Dict, Any

logger = logging.getLogger("orchestration.resource_managers")


class ResourceManager:
    """Manage resources"""
    
    def acquire(self, name: str) -> Any:
        raise NotImplementedError
    
    def release(self, name: str):
        raise NotImplementedError


class MemoryResourceManager(ResourceManager):
    """Memory resource manager"""
    
    def __init__(self):
        self.resources = {}
    
    def acquire(self, name: str) -> bytes:
        if name not in self.resources:
            self.resources[name] = b""
        return self.resources[name]
    
    def release(self, name: str):
        if name in self.resources:
            del self.resources[name]


class ConnectionPool:
    """Connection pool"""
    
    def __init__(self, factory, size: int = 10):
        self.factory = factory
        self.size = size
        self.available = []
        self.in_use = []
    
    def get(self):
        if self.available:
            conn = self.available.pop()
        else:
            conn = self.factory()
        self.in_use.append(conn)
        return conn
    
    def release(self, conn):
        if conn in self.in_use:
            self.in_use.remove(conn)
            if len(self.available) < self.size:
                self.available.append(conn)
