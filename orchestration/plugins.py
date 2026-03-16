"""Plugin system for extensibility"""

import os
import sys
import importlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import yaml

logger = logging.getLogger("orchestration.plugins")


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)


class Plugin(ABC):
    """Base plugin class"""
    
    metadata: PluginMetadata
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]):
        """Initialize plugin"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute plugin"""
        pass
    
    def shutdown(self):
        """Cleanup on shutdown"""
        pass


class PluginContext:
    """Plugin execution context"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.pipeline_state: Dict[str, Any] = {}
        self.event_bus = None
        self.cache = None
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value


class PluginManager:
    """Manage plugins"""
    
    def __init__(self, plugins_dir: str = "./plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self.plugins: Dict[str, Plugin] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.context = PluginContext()
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins"""
        discovered = []
        
        # Check plugins directory
        if self.plugins_dir.exists():
            for item in self.plugins_dir.iterdir():
                if item.is_dir() and (item / "plugin.py").exists():
                    discovered.append(item.name)
        
        # Check built-in plugins
        builtins = ["haskell", "qml", "reports", "cache", "metrics"]
        discovered.extend(builtins)
        
        return discovered
    
    def load_plugin(self, name: str) -> bool:
        """Load a plugin"""
        # Check if already loaded
        if name in self.plugins:
            return True
        
        # Try to load from plugins directory
        plugin_path = self.plugins_dir / name / "plugin.py"
        
        if plugin_path.exists():
            try:
                # Add to path
                sys.path.insert(0, str(self.plugins_dir / name))
                
                # Import plugin module
                module = importlib.import_module("plugin")
                
                # Get plugin class
                plugin_class = getattr(module, "Plugin", None)
                
                if plugin_class and issubclass(plugin_class, Plugin):
                    plugin = plugin_class()
                    self.plugins[name] = plugin
                    self.metadata[name] = plugin.metadata
                    
                    # Initialize
                    plugin.initialize(self.context)
                    
                    # Register hooks
                    for hook in plugin.metadata.hooks:
                        self.register_hook(hook, plugin.execute)
                    
                    logger.info(f"Loaded plugin: {name}")
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to load plugin {name}: {e}")
                return False
        
        # Try built-in
        return self._load_builtin_plugin(name)
    
    def _load_builtin_plugin(self, name: str) -> bool:
        """Load built-in plugin"""
        # Placeholder for built-in plugins
        logger.info(f"Built-in plugin: {name}")
        return True
    
    def unload_plugin(self, name: str):
        """Unload a plugin"""
        if name in self.plugins:
            plugin = self.plugins[name]
            plugin.shutdown()
            del self.plugins[name]
            
            if name in self.metadata:
                del self.metadata[name]
            
            logger.info(f"Unloaded plugin: {name}")
    
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        
        self.hooks[hook_name].append(callback)
    
    def trigger_hook(self, hook_name: str, *args, **kwargs):
        """Trigger all callbacks for a hook"""
        if hook_name not in self.hooks:
            return []
        
        results = []
        for callback in self.hooks[hook_name]:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook {hook_name} error: {e}")
        
        return results
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get loaded plugin"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins"""
        return [
            {
                "name": name,
                "metadata": {
                    "name": meta.name,
                    "version": meta.version,
                    "description": meta.description,
                    "author": meta.author,
                },
            }
            for name, meta in self.metadata.items()
        ]
    
    def load_config(self, config_path: str):
        """Load plugin configuration"""
        path = Path(config_path)
        
        if not path.exists():
            return
        
        config = yaml.safe_load(path.read_text()) or {}
        
        # Load enabled plugins
        for plugin_config in config.get("plugins", []):
            name = plugin_config.get("name")
            enabled = plugin_config.get("enabled", True)
            
            if enabled and name:
                self.load_plugin(name)


# Built-in plugin examples
class HaskellPlugin(Plugin):
    """Haskell conversion plugin"""
    
    metadata = PluginMetadata(
        name="haskell",
        version="1.0.0",
        description="Convert C++ to Haskell",
        hooks=["convert.haskell", "validate.haskell"],
    )
    
    def initialize(self, context: Dict[str, Any]):
        logger.info("Haskell plugin initialized")
    
    def execute(self, *args, **kwargs):
        return {"status": "converted", "format": "haskell"}


class QMLPlugin(Plugin):
    """QML conversion plugin"""
    
    metadata = PluginMetadata(
        name="qml",
        version="1.0.0",
        description="Convert C++ Qt to QML",
        hooks=["convert.qml", "validate.qml"],
    )
    
    def initialize(self, context: Dict[str, Any]):
        logger.info("QML plugin initialized")
    
    def execute(self, *args, **kwargs):
        return {"status": "converted", "format": "qml"}


class ReportsPlugin(Plugin):
    """Reports generation plugin"""
    
    metadata = PluginMetadata(
        name="reports",
        version="1.0.0",
        description="Generate Jasper/Pentaho reports",
        hooks=["convert.report", "validate.report"],
    )
    
    def initialize(self, context: Dict[str, Any]):
        logger.info("Reports plugin initialized")
    
    def execute(self, *args, **kwargs):
        return {"status": "generated", "format": "report"}


# Global plugin manager
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get plugin manager"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager