"""Cache invalidation strategies"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger("orchestration.cache_invalidation")


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    tags: list = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class CacheInvalidator:
    """Invalidate cache based on strategies"""
    
    def __init__(self):
        self.entries: Dict[str, CacheEntry] = {}
    
    def add(self, key: str, value: Any, ttl: int = None, tags: list = None):
        """Add entry"""
        now = time.time()
        expires = now + ttl if ttl else None
        
        self.entries[key] = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=expires,
            tags=tags or [],
        )
    
    def invalidate(self, key: str) -> bool:
        """Invalidate by key"""
        if key in self.entries:
            del self.entries[key]
            return True
        return False
    
    def invalidate_by_tag(self, tag: str):
        """Invalidate by tag"""
        to_delete = [
            key for key, entry in self.entries.items()
            if tag in entry.tags
        ]
        
        for key in to_delete:
            del self.entries[key]
    
    def invalidate_expired(self):
        """Invalidate expired entries"""
        now = time.time()
        expired = [
            key for key, entry in self.entries.items()
            if entry.expires_at and entry.expires_at < now
        ]
        
        for key in expired:
            del self.entries[key]
    
    def get_stats(self) -> Dict:
        """Get stats"""
        return {
            "total": len(self.entries),
            "expired": sum(
                1 for e in self.entries.values()
                if e.expires_at and e.expires_at < time.time()
            ),
        }
