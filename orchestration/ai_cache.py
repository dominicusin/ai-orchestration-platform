"""AI cache for LLM responses"""

import hashlib
import logging

logger = logging.getLogger("orchestration.ai_cache")


class AICache:
    """Cache LLM responses"""

    def __init__(self):
        self.cache: dict[str, str] = {}

    def _make_key(self, prompt: str, model: str) -> str:
        data = f"{model}:{prompt}"
        return hashlib.sha256(data.encode()).hexdigest()

    def get(self, prompt: str, model: str) -> str | None:
        key = self._make_key(prompt, model)
        return self.cache.get(key)

    def set(self, prompt: str, model: str, response: str):
        key = self._make_key(prompt, model)
        self.cache[key] = response

    def clear(self):
        self.cache.clear()


_ai_cache: AICache | None = None


def get_ai_cache() -> AICache:
    global _ai_cache
    if _ai_cache is None:
        _ai_cache = AICache()
    return _ai_cache
