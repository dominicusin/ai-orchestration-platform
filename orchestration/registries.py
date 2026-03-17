"""Pipeline registries"""

import logging
from typing import Dict, Any, Type

logger = logging.getLogger("orchestration.registries")


class Registry:
    """Base registry"""
    
    def __init__(self):
        self.items: Dict[str, Any] = {}
    
    def register(self, name: str, item: Any):
        self.items[name] = item
    
    def get(self, name: str) -> Any:
        return self.items.get(name)
    
    def list(self) -> list:
        return list(self.items.keys())


class ProviderRegistry(Registry):
    """AI provider registry"""
    pass


class ValidatorRegistry(Registry):
    """Validator registry"""
    pass


class RegistryFactory:
    """Create registries"""
    
    @staticmethod
    def create(name: str) -> Registry:
        if "provider" in name.lower():
            return ProviderRegistry()
        elif "validator" in name.lower():
            return ValidatorRegistry()
        return Registry()
