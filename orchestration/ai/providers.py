"""AI providers"""

from typing import Dict, Any, Optional


class BaseProvider:
    """Base AI provider"""
    
    name: str = "base"
    
    def complete(self, prompt: str) -> str:
        raise NotImplementedError


class OpenAIProvider(BaseProvider):
    name = "openai"
    
    def complete(self, prompt: str) -> str:
        return f"[OpenAI] {prompt[:50]}..."


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    
    def complete(self, prompt: str) -> str:
        return f"[Anthropic] {prompt[:50]}..."


class OllamaProvider(BaseProvider):
    name = "ollama"
    
    def complete(self, prompt: str) -> str:
        return f"[Ollama] {prompt[:50]}..."


PROVIDERS: Dict[str, type] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


def get_provider(name: str) -> Optional[BaseProvider]:
    """Get provider by name"""
    provider_class = PROVIDERS.get(name)
    if provider_class:
        return provider_class()
    return None


def list_providers() -> list:
    """List all providers"""
    return list(PROVIDERS.keys())