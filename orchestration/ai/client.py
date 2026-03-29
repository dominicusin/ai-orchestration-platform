"""
Async AI клиент с множественными провайдерами и Circuit Breaker
Заменяет ThreadPoolExecutor на asyncio для меньших накладных расходов.
"""

import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass, field
from enum import Enum

import aiohttp
import aiohttp.client_exceptions

from ..circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, get_breaker

logger = logging.getLogger("orchestration.ai")

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class AIConfig:
    """Конфигурация AI клиента"""
    # Модели
    groq_model: str = "llama-3.3-70b-versatile"
    cerebras_model: str = "llama-3.3-70b"
    hyperbolic_model: str = "meta-llama/Llama-3.3-70B-Instruct"
    gemini_model: str = "gemini-2.0-flash"
    ollama_model: str = "deepseek-coder:6.7b"
    huggingface_model: str = "meta-llama/Llama-3.3-70B-Instruct"

    # Параметры
    max_tokens: int = 8192
    temperature: float = 0.05
    max_retries: int = 3
    retry_base_delay: float = 1.0
    max_total_delay: float = 60.0

    # Rate limits per provider
    rate_limits: dict[str, int] = field(default_factory=lambda: {
        "groq": 30,      # requests/min
        "cerebras": 60,
        "hyperbolic": 30,
        "gemini": 15,
        "ollama": 999,   # local, no limit
        "huggingface": 30,
    })

    # Circuit breaker config per provider
    circuit_breaker_config: dict[str, dict] = field(default_factory=lambda: {
        "groq": {"failure_threshold": 5, "timeout": 30.0},
        "cerebras": {"failure_threshold": 5, "timeout": 30.0},
        "hyperbolic": {"failure_threshold": 5, "timeout": 30.0},
        "gemini": {"failure_threshold": 3, "timeout": 60.0},
        "ollama": {"failure_threshold": 10, "timeout": 10.0},
        "huggingface": {"failure_threshold": 5, "timeout": 30.0},
    })

    @classmethod
    def from_env(cls) -> "AIConfig":
        return cls(
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            cerebras_model=os.getenv("CEREBRAS_MODEL", "llama-3.3-70b"),
            hyperbolic_model=os.getenv("HYPERBOLIC_MODEL", "meta-llama/Llama-3.3-70B-Instruct"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            ollama_model=os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b"),
            huggingface_model=os.getenv("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct"),
            max_tokens=int(os.getenv("MAX_TOKENS", "8192")),
            temperature=float(os.getenv("TEMPERATURE", "0.05")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_base_delay=float(os.getenv("RETRY_BASE_DELAY", "1.0")),
            max_total_delay=float(os.getenv("MAX_TOTAL_DELAY", "60.0")),
        )


# ============================================================================
# МЕТРИКИ
# ============================================================================

@dataclass
class ProviderMetrics:
    """Метрики провайдера"""
    calls: int = 0
    errors: int = 0
    rate_limits: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    total_latency: float = 0.0

    COST_PER_MILLION = {
        "groq": 0.59,
        "cerebras": 0.60,
        "hyperbolic": 0.40,
        "gemini": 0.15,
        "ollama": 0.0,
        "huggingface": 0.0,
    }


@dataclass
class AIClientMetrics:
    """Общие метрики AI клиента"""
    calls: int = 0
    errors: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    providers: dict[str, ProviderMetrics] = field(default_factory=dict)

    def get_provider(self, name: str) -> ProviderMetrics:
        if name not in self.providers:
            self.providers[name] = ProviderMetrics()
        return self.providers[name]


# ============================================================================
# ASYNC AI CLIENT
# ============================================================================

class AsyncAIClient:
    """
    Async AI клиент с:
    - Множественными провайдерами
    - Circuit Breaker
    - Rate limiting per provider
    - Exponential backoff с jitter
    - Graceful degradation
    """

    def __init__(self, config: AIConfig = None):
        self.config = config or AIConfig.from_env()
        self.metrics = AIClientMetrics()

        # Circuit breakers для каждого провайдера
        self._breakers: dict[str, CircuitBreaker] = {}
        self._init_circuit_breakers()

        # Rate limiting
        self._rate_limiters: dict[str, asyncio.Semaphore] = {}
        self._rate_limit_last_reset: dict[str, float] = {}

        # HTTP session
        self._session: aiohttp.ClientSession | None = None

        # Clients
        self._groq = None
        self._gemini = None
        self._cerebras = None
        self._hyperbolic = None
        self._huggingface = None
        self._ollama = None

        self._init_clients()

    def _init_circuit_breakers(self):
        """Инициализация Circuit Breakers"""
        for provider, cb_config in self.config.circuit_breaker_config.items():
            self._breakers[provider] = get_breaker(
                provider,
                failure_threshold=cb_config.get("failure_threshold", 5),
                timeout=cb_config.get("timeout", 30.0),
            )
            logger.debug(f"Circuit breaker for {provider}: {cb_config}")

    def _init_clients(self):
        """Инициализация AI провайдеров"""
        logger.info("🔌 Инициализация AI провайдеров:")

        # Groq
        try:
            from groq import Groq
            key = os.getenv("GROQ_API_KEY")
            if key:
                self._groq = Groq(api_key=key)
                logger.info("   ✅ Groq")
        except ImportError:
            logger.warning("   ❌ Groq: библиотека не установлена")
        except Exception as e:
            logger.warning(f"   ❌ Groq: {e}")

        # Gemini
        try:
            from google import genai
            from google.genai import types
            key = os.getenv("GEMINI_API_KEY")
            if key:
                self._gemini = genai.Client(api_key=key)
                self._gemini_types = types
                logger.info("   ✅ Gemini")
        except ImportError:
            logger.warning("   ❌ Gemini: библиотека не установлена")
        except Exception as e:
            logger.warning(f"   ❌ Gemini: {e}")

        # Cerebras
        try:
            key = os.getenv("CEREBRAS_API_KEY")
            if key:
                from cerebras.cloud.sdk import Cerebras
                self._cerebras = Cerebras(api_key=key)
                logger.info("   ✅ Cerebras")
        except ImportError:
            logger.warning("   ❌ Cerebras: библиотека не установлена")
        except Exception as e:
            logger.warning(f"   ❌ Cerebras: {e}")

        # Hyperbolic
        key = os.getenv("HYPERBOLIC_API_KEY")
        if key:
            self._hyperbolic = {"api_key": key}
            logger.info("   ✅ Hyperbolic")

        # HuggingFace
        key = os.getenv("HF_TOKEN")
        if key:
            self._huggingface = {"token": key}
            logger.info("   ✅ HuggingFace")

        # Ollama - проверка сразу при инициализации
        try:
            url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            import urllib.request
            with urllib.request.urlopen(f"{url}/api/tags", timeout=2) as r:
                import json
                data = json.loads(r.read())
                models = [m["name"] for m in data.get("models", [])]
                self._ollama = {"url": url, "models": models}
                logger.info(f"   ✅ Ollama ({len(models)} моделей)")
        except Exception as e:
            self._ollama = None
            logger.warning(f"   ⚠️ Ollama: недоступен - {e}")

    async def _check_ollama(self):
        """Асинхронная проверка Ollama"""
        try:
            url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/api/tags", timeout=aiohttp.ClientTimeout(total=2)) as r:
                    if r.ok:
                        data = await r.json()
                        models = [m["name"] for m in data.get("models", [])]
                        self._ollama = {"url": url, "models": models}
                        logger.info(f"   ✅ Ollama ({len(models)} моделей)")
        except Exception as e:
            logger.warning(f"   ⚠️ Ollama: недоступен - {e}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание HTTP сессии"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _get_providers(self, task_type: str) -> list[str]:
        """Получение списка провайдеров для задачи"""
        # Ollama первым - локальный и бесплатный
        providers = []
        if self._ollama:
            providers.append("ollama")

        # Универсальные провайдеры из .env
        default_provider = os.getenv("DEFAULT_PROVIDER", "").lower()
        if default_provider and default_provider != "ollama":
            providers.append(default_provider)

        if task_type in ("sql",):
            providers.extend(["groq", "cerebras", "hyperbolic", "gemini", "deepseek", "cohere"])
        elif task_type in ("haskell", "qml"):
            providers.extend(["cerebras", "groq", "gemini", "deepseek", "mistral", "together"])
        elif task_type in ("analysis",):
            providers.extend(["gemini", "cerebras", "groq", "deepseek", "anthropic"])
        else:
            providers.extend(["cerebras", "groq", "gemini", "deepseek", "mistral"])

        return providers

    def _exponential_backoff(self, attempt: int, base_delay: float = None) -> float:
        """Exponential backoff с jitter и max delay"""
        if base_delay is None:
            base_delay = self.config.retry_base_delay

        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
        return min(delay, self.config.max_total_delay)

    async def _check_rate_limit(self, provider: str) -> bool:
        """Проверка rate limit для провайдера"""
        now = time.time()
        limit = self.config.rate_limits.get(provider, 30)

        # Сброс счётчика каждую минуту
        if now - self._rate_limit_last_reset.get(provider, 0) > 60:
            self._rate_limit_last_reset[provider] = now
            self._rate_limiters[provider] = asyncio.Semaphore(limit)

        if provider not in self._rate_limiters:
            self._rate_limiters[provider] = asyncio.Semaphore(limit)

        # Non-blocking acquire
        if self._rate_limiters[provider].locked():
            logger.warning(f"Rate limit reached for {provider}")
            return False
        return True

    async def call(
        self,
        prompt: str,
        model: str = "auto",
        max_tokens: int = None,
        timeout: float = 120.0
    ) -> str:
        """
        Выполнить асинхронный запрос к AI с fallback на другие провайдеры
        """
        if max_tokens is None:
            max_tokens = self.config.max_tokens

        providers = self._get_providers(model)
        last_error = None
        total_delay = 0.0

        for provider in providers:
            # Проверка Circuit Breaker
            breaker = self._breakers.get(provider)
            if breaker and not breaker.is_available:
                logger.debug(f"Circuit breaker OPEN for {provider}, skipping")
                continue

            # Rate limit check
            if not await self._check_rate_limit(provider):
                await asyncio.sleep(1)
                continue

            for attempt in range(self.config.max_retries):
                if total_delay >= self.config.max_total_delay:
                    logger.warning("Max total delay reached, stopping retries")
                    break

                try:
                    result = await self._call_provider(provider, prompt, max_tokens, timeout)
                    if result:
                        return result
                except CircuitBreakerOpenError:
                    # Быстрый fail
                    logger.debug(f"Circuit breaker OPEN for {provider}")
                    break
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()

                    if "429" in error_str or "rate_limit" in error_str:
                        self.metrics.get_provider(provider).rate_limits += 1
                        logger.warning(f"Rate limit {provider}, attempt {attempt + 1}")
                        delay = self._exponential_backoff(attempt)
                        await asyncio.sleep(delay)
                        total_delay += delay
                    elif "timeout" in error_str:
                        logger.debug(f"Timeout {provider}, attempt {attempt + 1}")
                        delay = self._exponential_backoff(attempt) * 0.5
                        await asyncio.sleep(delay)
                        total_delay += delay
                    else:
                        # Другая ошибка - пробуем следующий провайдер
                        logger.debug(f"{provider}: {str(e)[:60]}")
                        break

        logger.error(f"All providers failed: {last_error}")
        return ""

    async def _call_provider(
        self,
        provider: str,
        prompt: str,
        max_tokens: int,
        timeout: float
    ) -> str:
        """Вызов конкретного провайдера"""
        start_time = time.time()
        breaker = self._breakers.get(provider)

        try:
            if provider == "groq" and self._groq:
                await asyncio.sleep(0.5)
                resp = self._groq.chat.completions.create(
                    model=self.config.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=self.config.temperature,
                )
                tokens = resp.usage.total_tokens if hasattr(resp, 'usage') else 0
                self._record_call(provider, tokens, time.time() - start_time)
                if breaker:
                    breaker.record_success()
                return resp.choices[0].message.content or ""

            if provider == "cerebras" and self._cerebras:
                await asyncio.sleep(0.3)
                resp = self._cerebras.chat.completions.create(
                    model=self.config.cerebras_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                tokens = resp.usage.total_tokens if hasattr(resp, 'usage') else 0
                self._record_call(provider, tokens, time.time() - start_time)
                if breaker:
                    breaker.record_success()
                return resp.choices[0].message.content or ""

            if provider == "hyperbolic" and self._hyperbolic:
                await asyncio.sleep(0.3)
                session = await self._get_session()
                resp = await session.post(
                    "https://api.hyperbolic.xyz/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self._hyperbolic['api_key']}"},
                    json={
                        "model": self.config.hyperbolic_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                    },
                    timeout=aiohttp.ClientTimeout(total=60),
                )
                if resp.ok:
                    data = await resp.json()
                    tokens = data.get('usage', {}).get('total_tokens', 0)
                    self._record_call(provider, tokens, time.time() - start_time)
                    if breaker:
                        breaker.record_success()
                    return data["choices"][0]["message"]["content"]

            if provider == "gemini" and self._gemini:
                await asyncio.sleep(1)
                resp = self._gemini.models.generate_content(
                    model=self.config.gemini_model,
                    contents=prompt,
                    config=self._gemini_types.GenerateContentConfig(
                        max_output_tokens=max_tokens,
                        temperature=self.config.temperature
                    ),
                )
                self._record_call(provider, 0, time.time() - start_time)
                if breaker:
                    breaker.record_success()
                return resp.text or ""

            if provider == "ollama":
                if not self._ollama:
                    raise Exception("Ollama not available")

                session = await self._get_session()
                resp = await session.post(
                    f"{self._ollama['url']}/api/generate",
                    json={
                        "model": self.config.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_ctx": 8192},
                    },
                    timeout=aiohttp.ClientTimeout(total=300),
                )
                if resp.ok:
                    data = await resp.json()
                    self._record_call(provider, 0, time.time() - start_time)
                    if breaker:
                        breaker.record_success()
                    return data.get("response", "")

            if provider == "huggingface" and self._huggingface:
                session = await self._get_session()
                resp = await session.post(
                    f"https://api-inference.huggingface.co/models/{self.config.huggingface_model}",
                    headers={"Authorization": f"Bearer {self._huggingface['token']}"},
                    json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}},
                    timeout=aiohttp.ClientTimeout(total=60),
                )
                if resp.ok:
                    data = await resp.json()
                    self._record_call(provider, 0, time.time() - start_time)
                    if breaker:
                        breaker.record_success()
                    return data[0]["generated_text"]

            # Универсальный провайдер (DeepSeek, Mistral, Cohere, и др.)
            from .providers import OPENAI_COMPATIBLE_PROVIDERS
            if provider in OPENAI_COMPATIBLE_PROVIDERS:
                config = OPENAI_COMPATIBLE_PROVIDERS[provider]
                api_key = os.getenv(config.api_key_env)
                if api_key:
                    session = await self._get_session()
                    url = f"{config.base_url}/chat/completions"
                    resp = await session.post(
                        url,
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={
                            "model": config.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": max_tokens,
                        },
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    )
                    if resp.ok:
                        data = await resp.json()
                        self._record_call(provider, 0, time.time() - start_time)
                        if breaker:
                            breaker.record_success()
                        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

            raise Exception(f"Provider {provider} not available")

        except Exception as e:
            if breaker:
                breaker.record_failure(str(e))
            raise

    def _record_call(self, provider: str, tokens: int, latency: float):
        """Запись метрик вызова"""
        pm = self.metrics.get_provider(provider)
        pm.calls += 1
        pm.total_tokens += tokens
        pm.total_latency += latency

        cost = (tokens / 1_000_000) * pm.COST_PER_MILLION.get(provider, 0)
        pm.total_cost += cost

        self.metrics.calls += 1
        self.metrics.total_tokens += tokens
        self.metrics.total_cost += cost

    async def call_batch(
        self,
        prompts: list[dict],
        model: str = "auto",
        max_concurrent: int = 4
    ) -> list[dict]:
        """Параллельная обработка нескольких промптов"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def worker(idx: int, prompt: str, op: str) -> tuple:
            async with semaphore:
                result = await self.call(prompt, model)
                return idx, op, result

        tasks = [
            worker(idx, p.get("prompt", ""), p.get("operation", "default"))
            for idx, p in enumerate(prompts)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = [None] * len(prompts)
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Batch error: {r}")
                continue
            idx, op, result = r
            output[idx] = {"operation": op, "result": result}

        return output

    def get_status(self) -> dict:
        """Получение статуса всех провайдеров"""
        return {
            "metrics": {
                "total_calls": self.metrics.calls,
                "total_tokens": self.metrics.total_tokens,
                "total_cost": self.metrics.total_cost,
                "by_provider": {
                    name: {
                        "calls": pm.calls,
                        "errors": pm.errors,
                        "rate_limits": pm.rate_limits,
                        "total_tokens": pm.total_tokens,
                        "total_cost": pm.total_cost,
                        "avg_latency": pm.total_latency / pm.calls if pm.calls > 0 else 0,
                    }
                    for name, pm in self.metrics.providers.items()
                }
            },
        }

    async def close(self):
        """Закрытие сессии"""
        if self._session and not self._session.closed:
            await self._session.close()


# ============================================================================
# FALLBACK TEMPLATES
# ============================================================================

FALLBACK_TEMPLATES = {
    "haskell": """module {name} where

import Data.Text (Text)
import Data.Maybe (Maybe(..))

-- Auto-generated from C++ struct
data {name} = {name}
    {{ {fields} }}
    deriving (Show, Eq)

-- Placeholder functions
{name} :: {name}
{name} = {name} {{ {defaults} }}
""",
    "sql": """-- {name}
CREATE TABLE IF NOT EXISTS {table_name} (
    id SERIAL PRIMARY KEY,
    {columns}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
}
