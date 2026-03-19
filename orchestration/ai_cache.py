"""AI cache for LLM responses"""

import hashlib
import json
import logging
from typing import Optional, Dict

logger = logging.getLogger("orchestration.ai_cache")


class AICache:
    """Cache LLM responses"""
    
    def __init__(self):
        self.cache: Dict[str, str] = {}
    
    def _make_key(self, prompt: str, model: str) -> str:
        data = f"{model}:{prompt}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get(self, prompt: str, model: str) -> Optional[str]:
        key = self._make_key(prompt, model)
        return self.cache.get(key)
    
    def set(self, prompt: str, model: str, response: str):
        key = self._make_key(prompt, model)
        self.cache[key] = response
    
    def clear(self):
        self.cache.clear()


_ai_cache: Optional[AICache] = None


def get_ai_cache() -> AICache:
    global _ai_cache
    if _ai_cache is None:
        _ai_cache = AICache()
    return _ai_cache