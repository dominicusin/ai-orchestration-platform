"""Cache manager with multiple backends"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("orchestration.cache_manager")


class CacheBackend(Enum):
    """Cache backend types"""
    MEMORY = "memory"
    DISK = "disk"
    REDIS = "redis"
    MEMCACHED = "memcached"


@dataclass
class CacheEntry:
    """Cache entry"""
    key: str
    value: Any
    created_at: str
    expires_at: Optional[str] = None
    hits: int = 0
    size: int = 0


class MemoryCache:
    """In-memory cache"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if entry.expires_at:
            exp = datetime.fromisoformat(entry.expires_at)
            if datetime.now() > exp:
                del self.cache[key]
                return None
        
        entry.hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set value"""
        # Evict if full
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        expires = None
        if ttl or self.ttl:
            expires = (datetime.now() + timedelta(seconds=ttl or self.ttl)).isoformat()
        
        self.cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now().isoformat(),
            expires_at=expires,
            size=len(str(value)),
        )
    
    def delete(self, key: str):
        """Delete key"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all"""
        self.cache = {}
    
    def _evict_lru(self):
        """Evict least recently used"""
        if not self.cache:
            return
        
        # Find entry with lowest hits
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].hits)
        del self.cache[lru_key]
    
    def stats(self) -> Dict:
        """Get cache stats"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_hits": sum(e.hits for e in self.cache.values()),
        }


class DiskCache:
    """Disk-based cache"""
    
    def __init__(self, cache_dir: str = "./cache", max_size_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size_mb * 1024 * 1024
    
    def _get_path(self, key: str) -> Path:
        """Get cache file path"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value"""
        path = self._get_path(key)
        
        if not path.exists():
            return None
        
        try:
            data = json.loads(path.read_text())
            
            # Check expiration
            if data.get("expires_at"):
                exp = datetime.fromisoformat(data["expires_at"])
                if datetime.now() > exp:
                    path.unlink()
                    return None
            
            return data.get("value")
            
        except Exception as e:
            logger.error(f"Disk cache read error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set value"""
        expires = None
        if ttl:
            expires = (datetime.now() + timedelta(seconds=ttl)).isoformat()
        
        data = {
            "key": key,
            "value": value,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires,
        }
        
        path = self._get_path(key)
        
        try:
            path.write_text(json.dumps(data))
            
            # Check size limit
            self._check_size()
            
        except Exception as e:
            logger.error(f"Disk cache write error: {e}")
    
    def delete(self, key: str):
        """Delete key"""
        path = self._get_path(key)
        if path.exists():
            path.unlink()
    
    def clear(self):
        """Clear all"""
        for f in self.cache_dir.glob("*.json"):
            f.unlink()
    
    def _check_size(self):
        """Check and enforce size limit"""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        
        if total_size > self.max_size:
            # Delete oldest files
            files = sorted(
                self.cache_dir.glob("*.json"),
                key=lambda f: f.stat().st_mtime
            )
            
            for f in files[:int(len(files) * 0.2)]:
                f.unlink()
    
    def stats(self) -> Dict:
        """Get cache stats"""
        files = list(self.cache_dir.glob("*.json"))
        return {
            "size": len(files),
            "total_size_mb": sum(f.stat().st_size for f in files) / 1024 / 1024,
        }


class MultiLevelCache:
    """Multi-level cache (L1 memory, L2 disk)"""
    
    def __init__(self, l1_size: int = 100, l2_dir: str = "./cache", l2_ttl: int = 86400):
        self.l1 = MemoryCache(max_size=l1_size)
        self.l2 = DiskCache(cache_dir=l2_dir)
        self.l2_ttl = l2_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get from L1, then L2"""
        # Try L1
        value = self.l1.get(key)
        if value is not None:
            return value
        
        # Try L2
        value = self.l2.get(key)
        if value is not None:
            # Promote to L1
            self.l1.set(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set in both levels"""
        self.l1.set(key, value)
        self.l2.set(key, value, ttl or self.l2_ttl)
    
    def delete(self, key: str):
        """Delete from both levels"""
        self.l1.delete(key)
        self.l2.delete(key)
    
    def clear(self):
        """Clear both levels"""
        self.l1.clear()
        self.l2.clear()
    
    def stats(self) -> Dict:
        """Get combined stats"""
        return {
            "l1": self.l1.stats(),
            "l2": self.l2.stats(),
        }


class CacheManager:
    """Unified cache manager"""
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        backend = config.get("backend", "multi")
        
        if backend == "memory":
            self.cache = MemoryCache(
                max_size=config.get("max_size", 1000),
                ttl=config.get("ttl", 3600),
            )
        elif backend == "disk":
            self.cache = DiskCache(
                cache_dir=config.get("cache_dir", "./cache"),
                max_size_mb=config.get("max_size_mb", 100),
            )
        else:  # multi
            self.cache = MultiLevelCache(
                l1_size=config.get("l1_size", 100),
                l2_dir=config.get("cache_dir", "./cache"),
                l2_ttl=config.get("ttl", 86400),
            )
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set cached value"""
        self.cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """Delete cached value"""
        self.cache.delete(key)
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
    
    def stats(self) -> Dict:
        """Get cache stats"""
        return self.cache.stats()


# Global cache manager
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(config: Dict = None) -> CacheManager:
    """Get cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(config)
    return _cache_manager
