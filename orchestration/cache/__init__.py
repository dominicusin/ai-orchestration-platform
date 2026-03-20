"""Cache module"""

import time
from typing import Any, Optional, Dict


class Cache:
    """Simple cache"""
    
    def __init__(self):
        self.store: Dict[str, Any] = {}
    
    def get(self, key: str) -> Optional[Any]:
        return self.store.get(key)
    
    def set(self, key: str, value: Any):
        self.store[key] = value
    
    def delete(self, key: str):
        self.store.pop(key, None)
    
    def clear(self):
        self.store.clear()


def get_cache() -> Cache:
    return Cache()