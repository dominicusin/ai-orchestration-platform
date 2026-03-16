"""Redis cache backend for distributed caching"""

import os
import json
import logging
from typing import Any, Optional, Dict
from datetime import timedelta
import hashlib

logger = logging.getLogger("orchestration.redis_cache")


class RedisCache:
    """Redis-based distributed cache"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client = None
        self._connected = False
    
    def _get_client(self):
        """Get or create Redis client"""
        if self._client is None:
            try:
                import redis.asyncio as redis
                self._client = redis.from_url(
                    self.connection_string,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except ImportError:
                logger.warning("redis-py not installed")
                return None
        return self._client
    
    async def connect(self) -> bool:
        """Connect to Redis"""
        try:
            client = self._get_client()
            if client is None:
                return False
            
            await client.ping()
            self._connected = True
            logger.info(f"Connected to Redis: {self.connection_string}")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self._connected = False
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return None
        
        try:
            client = self._get_client()
            value = await client.get(key)
            
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return False
        
        try:
            client = self._get_client()
            
            # Serialize
            if not isinstance(value, str):
                serialized = json.dumps(value)
            else:
                serialized = value
            
            await client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        if not self._connected:
            return False
        
        try:
            client = self._get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._connected:
            return False
        
        try:
            client = self._get_client()
            return await client.exists(key) > 0
        except Exception:
            return False
    
    async def clear(self) -> bool:
        """Clear all cache"""
        if not self._connected:
            return False
        
        try:
            client = self._get_client()
            await client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def get_stats(self) -> Dict:
        """Get cache statistics"""
        if not self._connected:
            return {"connected": False}
        
        try:
            client = self._get_client()
            info = await client.info("stats")
            
            return {
                "connected": True,
                "keys": await client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "memory": info.get("used_memory_human", "N/A"),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    async def close(self):
        """Close connection"""
        if self._client:
            await self._client.close()
            self._connected = False


class DistributedCacheManager:
    """Manage distributed caching with Redis"""
    
    def __init__(self):
        self.redis = RedisCache()
        self.memory_cache: Dict[str, Any] = {}
        self.fallback_to_memory = True
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (Redis first, then memory)"""
        # Try Redis
        value = await self.redis.get(key)
        if value is not None:
            return value
        
        # Fallback to memory
        if self.fallback_to_memory:
            return self.memory_cache.get(key)
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set in both Redis and memory"""
        # Memory cache (always)
        self.memory_cache[key] = value
        
        # Redis (async)
        await self.redis.set(key, value, ttl)
    
    async def delete(self, key: str):
        """Delete from both caches"""
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        await self.redis.delete(key)
    
    async def clear(self):
        """Clear all caches"""
        self.memory_cache = {}
        await self.redis.clear()
    
    def get_stats(self) -> Dict:
        """Get combined stats"""
        return {
            "memory_keys": len(self.memory_cache),
            "redis": {"connected": self.redis._connected},
        }


# Global instance
_redis_cache: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Get Redis cache instance"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache
