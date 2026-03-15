"""RLM (Recursive Language Models) wrapper for long-context processing"""

import os
from typing import Optional, Any
from dataclasses import dataclass

try:
    from rlm_toolkit import RLM, RLMConfig
    from rlm_toolkit.providers import OllamaProvider, OpenAIProvider, GroqProvider
    RLM_AVAILABLE = True
except ImportError:
    RLM_AVAILABLE = False
    RLM = None
    RLMConfig = None
    OllamaProvider = None
    OpenAIProvider = None
    GroqProvider = None

from orchestration.ai.client import AsyncAIClient, AIConfig


@dataclass
class RLMResult:
    """Результат RLM вызова"""
    answer: str
    cost: float
    iterations: int
    tokens_used: int


class RLMWrapper:
    """
    Wrapper around RLM-Toolkit для обработки длинных контекстов.
    
    Использует Recursive Language Models паттерн:
    - Root LM получает только query
    - Python REPL хранит контекст как переменную
    - Sub-LM вызываются рекурсивно для частей контекста
    """
    
    def __init__(self, ai_client: AsyncAIClient):
        if not RLM_AVAILABLE:
            raise ImportError("rlm_toolkit not installed")
        
        self.ai = ai_client
        self._rlm: Optional[RLM] = None
        self._config = self._build_config()
    
    def _build_config(self) -> RLMConfig:
        """Создаёт конфигурацию RLM"""
        if RLMConfig is None:
            raise ImportError("rlm_toolkit not installed")
        return RLMConfig(
            max_cost=float(os.getenv("RLM_MAX_COST", "10.0")),
            sandbox=os.getenv("RLM_SANDBOX", "true").lower() == "true",
            use_infiniretri=os.getenv("RLM_USE_INFINIRETRI", "false").lower() == "true",
            infiniretri_threshold=int(os.getenv("RLM_INFINIRETRI_THRESHOLD", "100000")),
            max_depth=int(os.getenv("RLM_MAX_DEPTH", "2")),
            max_execution_time=float(os.getenv("RLM_MAX_TIME", "30.0")),
            max_iterations=int(os.getenv("RLM_MAX_ITERATIONS", "50")),
        )
    
    def _get_root_provider(self):
        """Root provider - мощная модель для финального ответа"""
        provider = os.getenv("RLM_ROOT_PROVIDER", "groq").lower()
        
        if provider == "groq":
            return GroqProvider(
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                api_key=os.getenv("GROQ_API_KEY", ""),
            )
        elif provider == "openai":
            return OpenAIProvider(
                model=os.getenv("OPENAI_MODEL", "gpt-5"),
                api_key=os.getenv("OPENAI_API_KEY", ""),
            )
        elif provider == "ollama":
            return OllamaProvider(
                model=os.getenv("OLLAMA_MODEL", "qwen2.5:72b"),
                base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            )
        else:
            raise ValueError(f"Unknown root provider: {provider}")
    
    def _get_sub_provider(self):
        """Sub provider - быстрая/дешёвая модель для подзадач"""
        provider = os.getenv("RLM_SUB_PROVIDER", "ollama").lower()
        
        if provider == "ollama":
            return OllamaProvider(
                model=os.getenv("OLLAMA_SUB_MODEL", "qwen2.5:7b"),
                base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            )
        elif provider == "groq":
            return GroqProvider(
                model=os.getenv("GROQ_SUB_MODEL", "llama-3.1-8b-instant"),
                api_key=os.getenv("GROQ_API_KEY", ""),
            )
        else:
            raise ValueError(f"Unknown sub provider: {provider}")
    
    def initialize(self) -> bool:
        """Инициализирует RLM провайдеры"""
        try:
            self._rlm = RLM(
                root=self._get_root_provider(),
                sub=self._get_sub_provider(),
                config=self._config,
            )
            return True
        except Exception as e:
            print(f"RLM init failed: {e}")
            return False
    
    def run(self, context: str, query: str) -> RLMResult:
        """
        Запускает RLM обработку контекста.
        
        Args:
            context: Большой контекст (код, документы, etc)
            query: Вопрос к контексту
            
        Returns:
            RLMResult с ответом, стоимостью и итерациями
        """
        if not self._rlm:
            if not self.initialize():
                raise RuntimeError("RLM not initialized")
        
        result = self._rlm.run(context, query)
        
        return RLMResult(
            answer=result.answer if hasattr(result, 'answer') else str(result),
            cost=result.cost if hasattr(result, 'cost') else 0.0,
            iterations=result.iterations if hasattr(result, 'iterations') else 1,
            tokens_used=result.tokens if hasattr(result, 'tokens') else 0,
        )
    
    async def run_async(self, context: str, query: str) -> RLMResult:
        """Async wrapper для RLM"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, context, query)


def create_rlm_wrapper(ai_client: AsyncAIClient) -> Optional[RLMWrapper]:
    """Factory для создания RLM wrapper"""
    if os.getenv("ENABLE_RLM", "false").lower() != "true":
        return None
    
    wrapper = RLMWrapper(ai_client)
    if wrapper.initialize():
        return wrapper
    return None
