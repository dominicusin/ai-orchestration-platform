"""Plugin system for extensibility"""

import logging
from typing import Dict, Any, Callable

logger = logging.getLogger("orchestration.plugins")


class Plugin:
    """Base plugin"""
    
    name: str = ""
    version: str = "1.0"
    
    def initialize(self, context: Dict):
        """Initialize plugin"""
        pass
    
    def execute(self, *args, **kwargs):
        """Execute plugin"""
        raise NotImplementedError


class PluginManager:
    """Manage plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
    
    def register(self, plugin: Plugin):
        """Register plugin"""
        self.plugins[plugin.name] = plugin
        logger.info(f"Registered plugin: {plugin.name}")
    
    def get(self, name: str) -> Plugin:
        """Get plugin"""
        return self.plugins.get(name)
    
    def execute(self, name: str, *args, **kwargs):
        """Execute plugin"""
        plugin = self.get(name)
        if plugin:
            return plugin.execute(*args, **kwargs)
        raise ValueError(f"Plugin not found: {name}")


# Global plugin manager
_plugin_manager = None


def get_plugin_manager() -> PluginManager:
    """Get plugin manager"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
