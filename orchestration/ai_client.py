"""
AI Client for LLM integration
Клиент для интеграции с LLM
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class LLMProvider(Enum):
    """Провайдеры LLM"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    MISTRAL = "mistral"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    COHERE = "cohere"


@dataclass
class LLMResponse:
    """Ответ от LLM"""
    content: str
    model: str
    provider: LLMProvider
    tokens_used: int = 0
    latency: float = 0.0
    finish_reason: str = "stop"
    metadata: dict = field(default_factory=dict)


@dataclass
class LLMMetrics:
    """Метрики LLM"""
    provider: LLMProvider
    model: str
    avg_latency: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0


class BaseLLMClient(ABC):
    """Базовый класс LLM клиента"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self._metrics: dict[str, LLMMetrics] = {}

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Генерация текста"""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ):
        """Генерация текста потоково"""
        pass

    def get_metrics(self, provider: LLMProvider) -> LLMMetrics | None:
        """Получение метрик"""
        return self._metrics.get(provider.value)


class OpenAIClient(BaseLLMClient):
    """OpenAI клиент"""

    def __init__(self, api_key: str = None, base_url: str = None):
        super().__init__(api_key, base_url)
        self.provider = LLMProvider.OPENAI

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        start = time.time()

        # Simulate API call
        await asyncio.sleep(0.1)

        content = f"[OpenAI {model}] Response to: {prompt[:50]}..."
        latency = time.time() - start

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            tokens_used=len(prompt) + len(content),
            latency=latency,
        )

    async def generate_stream(self, prompt: str, model: str = "gpt-4o-mini", **kwargs):
        """Stream generation"""
        response = await self.generate(prompt, model, **kwargs)
        for char in response.content:
            yield char
            await asyncio.sleep(0.01)


class OllamaClient(BaseLLMClient):
    """Ollama клиент (бесплатный, локальный)"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        super().__init__(base_url=base_url)
        self.provider = LLMProvider.OLLAMA

    async def generate(
        self,
        prompt: str,
        model: str = "llama3.2",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        start = time.time()

        # Simulate local model inference
        await asyncio.sleep(0.05)

        content = f"[Ollama {model}] Response to: {prompt[:50]}..."
        latency = time.time() - start

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            tokens_used=len(prompt) + len(content),
            latency=latency,
        )

    async def generate_stream(self, prompt: str, model: str = "llama3.2", **kwargs):
        """Stream generation"""
        response = await self.generate(prompt, model, **kwargs)
        for char in response.content:
            yield char
            await asyncio.sleep(0.005)


class GroqClient(BaseLLMClient):
    """Groq клиент (бесплатный, быстрый)"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.provider = LLMProvider.GROQ

    async def generate(
        self,
        prompt: str,
        model: str = "llama-3.3-70b-versatile",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        start = time.time()

        # Groq is known for fast inference
        await asyncio.sleep(0.03)

        content = f"[Groq {model}] Response to: {prompt[:50]}..."
        latency = time.time() - start

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            tokens_used=len(prompt) + len(content),
            latency=latency,
        )

    async def generate_stream(self, prompt: str, model: str = "llama-3.3-70b-versatile", **kwargs):
        """Stream generation"""
        response = await self.generate(prompt, model, **kwargs)
        for char in response.content:
            yield char
            await asyncio.sleep(0.003)


class DeepSeekClient(BaseLLMClient):
    """DeepSeek клиент (бесплатный)"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.provider = LLMProvider.DEEPSEEK

    async def generate(
        self,
        prompt: str,
        model: str = "deepseek-chat",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        start = time.time()

        await asyncio.sleep(0.08)

        content = f"[DeepSeek {model}] Response to: {prompt[:50]}..."
        latency = time.time() - start

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            tokens_used=len(prompt) + len(content),
            latency=latency,
        )

    async def generate_stream(self, prompt: str, model: str = "deepseek-chat", **kwargs):
        """Stream generation"""
        response = await self.generate(prompt, model, **kwargs)
        for char in response.content:
            yield char
            await asyncio.sleep(0.008)


class MistralClient(BaseLLMClient):
    """Mistral AI клиент"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.provider = LLMProvider.MISTRAL

    async def generate(
        self,
        prompt: str,
        model: str = "mistral-small-latest",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        start = time.time()

        await asyncio.sleep(0.12)

        content = f"[Mistral {model}] Response to: {prompt[:50]}..."
        latency = time.time() - start

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            tokens_used=len(prompt) + len(content),
            latency=latency,
        )

    async def generate_stream(self, prompt: str, model: str = "mistral-small-latest", **kwargs):
        """Stream generation"""
        response = await self.generate(prompt, model, **kwargs)
        for char in response.content:
            yield char
            await asyncio.sleep(0.01)


class CohereClient(BaseLLMClient):
    """Cohere клиент"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.provider = LLMProvider.COHERE

    async def generate(
        self,
        prompt: str,
        model: str = "command-r-plus",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        start = time.time()

        await asyncio.sleep(0.09)

        content = f"[Cohere {model}] Response to: {prompt[:50]}..."
        latency = time.time() - start

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            tokens_used=len(prompt) + len(content),
            latency=latency,
        )

    async def generate_stream(self, prompt: str, model: str = "command-r-plus", **kwargs):
        """Stream generation"""
        response = await self.generate(prompt, model, **kwargs)
        for char in response.content:
            yield char
            await asyncio.sleep(0.009)


class LLMManager:
    """Менеджер LLM клиентов"""

    def __init__(self):
        self._clients: dict[LLMProvider, BaseLLMClient] = {}

    def register_client(self, provider: LLMProvider, client: BaseLLMClient):
        """Регистрация клиента"""
        self._clients[provider] = client

    def get_client(self, provider: LLMProvider) -> BaseLLMClient | None:
        """Получение клиента"""
        return self._clients.get(provider)

    def get_available_providers(self) -> list[LLMProvider]:
        """Список доступных провайдеров"""
        return list(self._clients.keys())


# Rating system for free LLMs
class LLMRater:
    """Рейтинг LLM"""

    # Ratings based on typical performance
    RATINGS = {
        LLMProvider.OLLAMA: {"speed": 9, "quality": 7, "cost": 10},  # Free, local
        LLMProvider.GROQ: {"speed": 10, "quality": 8, "cost": 10},  # Free tier fast
        LLMProvider.DEEPSEEK: {"speed": 7, "quality": 8, "cost": 10},  # Free API
        LLMProvider.COHERE: {"speed": 6, "quality": 8, "cost": 5},  # Limited free
        LLMProvider.MISTRAL: {"speed": 6, "quality": 8, "cost": 5},  # Limited free
        LLMProvider.OPENAI: {"speed": 7, "quality": 9, "cost": 2},  # Paid
        LLMProvider.ANTHROPIC: {"speed": 7, "quality": 9, "cost": 2},  # Paid
    }

    @classmethod
    def get_rating(cls, provider: LLMProvider) -> dict[str, float]:
        """Получение рейтинга провайдера"""
        return cls.RATINGS.get(provider, {"speed": 0, "quality": 0, "cost": 0})

    @classmethod
    def rank_by_speed(cls) -> list[tuple]:
        """Рейтинг по скорости"""
        return sorted(
            cls.RATINGS.items(),
            key=lambda x: x[1]["speed"],
            reverse=True
        )

    @classmethod
    def rank_by_quality(cls) -> list[tuple]:
        """Рейтинг по качеству"""
        return sorted(
            cls.RATINGS.items(),
            key=lambda x: x[1]["quality"],
            reverse=True
        )

    @classmethod
    def rank_by_cost(cls) -> list[tuple]:
        """Рейтинг по стоимости (бесплатные выше)"""
        return sorted(
            cls.RATINGS.items(),
            key=lambda x: x[1]["cost"],
            reverse=True
        )

    @classmethod
    def rank_overall(cls) -> list[tuple]:
        """Общий рейтинг (бесплатные + скорость + качество)"""
        def score(item):
            _, ratings = item
            # Weight: cost (free) 40%, speed 30%, quality 30%
            return ratings["cost"] * 0.4 + ratings["speed"] * 0.3 + ratings["quality"] * 0.3

        return sorted(cls.RATINGS.items(), key=score, reverse=True)


# Singleton
_llm_manager: LLMManager | None = None


def get_llm_manager() -> LLMManager:
    """Получение менеджера LLM"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
        # Register default clients
        _llm_manager.register_client(LLMProvider.OLLAMA, OllamaClient())
        _llm_manager.register_client(LLMProvider.GROQ, GroqClient())
        _llm_manager.register_client(LLMProvider.DEEPSEEK, DeepSeekClient())
        _llm_manager.register_client(LLMProvider.MISTRAL, MistralClient())
        _llm_manager.register_client(LLMProvider.COHERE, CohereClient())
    return _llm_manager
