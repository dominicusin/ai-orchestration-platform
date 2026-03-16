"""AI response cache with semantic hashing"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("orchestration.ai_cache")


class SemanticCache:
    """Cache AI responses with semantic matching"""
    
    def __init__(self, cache_dir: str = "./cache/ai", ttl: int = 86400):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.ttl = ttl
        self.index_file = self.cache_dir / "index.json"
        self.index: Dict[str, Dict] = self._load_index()
    
    def _load_index(self) -> Dict:
        """Load cache index"""
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text())
            except:
                return {}
        return {}
    
    def _save_index(self):
        """Save cache index"""
        self.index_file.write_text(json.dumps(self.index, indent=2))
    
    def _hash_prompt(self, prompt: str) -> str:
        """Create semantic hash of prompt"""
        # Normalize prompt
        normalized = prompt.lower().strip()
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        # Create hash
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _get_cache_path(self, prompt_hash: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{prompt_hash}.json"
    
    def get(self, prompt: str) -> Optional[Dict]:
        """Get cached response"""
        prompt_hash = self._hash_prompt(prompt)
        
        if prompt_hash not in self.index:
            return None
        
        cache_path = self._get_cache_path(prompt_hash)
        
        if not cache_path.exists():
            del self.index[prompt_hash]
            return None
        
        try:
            data = json.loads(cache_path.read_text())
            
            # Check expiration
            created = datetime.fromisoformat(data["created_at"])
            if datetime.now() - created > timedelta(seconds=self.ttl):
                # Expired
                cache_path.unlink()
                del self.index[prompt_hash]
                self._save_index()
                return None
            
            # Update access stats
            self.index[prompt_hash]["access_count"] = self.index[prompt_hash].get("access_count", 0) + 1
            self.index[prompt_hash]["last_access"] = datetime.now().isoformat()
            self._save_index()
            
            return data
            
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            return None
    
    def set(self, prompt: str, response: str, metadata: Dict = None):
        """Cache response"""
        prompt_hash = self._hash_prompt(prompt)
        
        cache_data = {
            "prompt": prompt,
            "response": response,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        
        cache_path = self._get_cache_path(prompt_hash)
        cache_path.write_text(json.dumps(cache_data, indent=2))
        
        # Update index
        self.index[prompt_hash] = {
            "prompt_hash": prompt_hash,
            "created_at": cache_data["created_at"],
            "access_count": 0,
            "last_access": None,
        }
        
        self._save_index()
        
        logger.debug(f"Cached response for prompt: {prompt_hash}")
    
    def delete(self, prompt: str):
        """Delete cached response"""
        prompt_hash = self._hash_prompt(prompt)
        
        cache_path = self._get_cache_path(prompt_hash)
        if cache_path.exists():
            cache_path.unlink()
        
        if prompt_hash in self.index:
            del self.index[prompt_hash]
            self._save_index()
    
    def clear(self):
        """Clear all cache"""
        for f in self.cache_dir.glob("*.json"):
            if f != self.index_file:
                f.unlink()
        
        self.index = {}
        self._save_index()
        
        logger.info("AI cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_entries = len(self.index)
        total_size = sum(
            f.stat().st_size 
            for f in self.cache_dir.glob("*.json") 
            if f != self.index_file
        )
        
        total_accesses = sum(
            entry.get("access_count", 0) 
            for entry in self.index.values()
        )
        
        return {
            "entries": total_entries,
            "size_bytes": total_size,
            "size_mb": total_size / 1024 / 1024,
            "total_accesses": total_accesses,
        }


class PromptCache:
    """Cache for prompt templates"""
    
    def __init__(self):
        self.cache: Dict[str, str] = {}
    
    def get(self, key: str) -> Optional[str]:
        """Get cached prompt"""
        return self.cache.get(key)
    
    def set(self, key: str, prompt: str):
        """Cache prompt"""
        self.cache[key] = prompt
    
    def clear(self):
        """Clear cache"""
        self.cache = {}


# Global instances
_ai_cache: Optional[SemanticCache] = None
_prompt_cache: Optional[PromptCache] = None


def get_ai_cache() -> SemanticCache:
    """Get AI response cache"""
    global _ai_cache
    if _ai_cache is None:
        _ai_cache = SemanticCache()
    return _ai_cache


def get_prompt_cache() -> PromptCache:
    """Get prompt cache"""
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = PromptCache()
    return _prompt_cache
