"""AI module"""

from typing import Dict, Any, List


class AIClient:
    """AI client stub"""
    
    def __init__(self, provider: str = "openai"):
        self.provider = provider
    
    def complete(self, prompt: str) -> str:
        return f"Response from {self.provider}"


def get_client(provider: str = "openai") -> AIClient:
    return AIClient(provider)