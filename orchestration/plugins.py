"""Plugin system for extensibility"""

import os
import importlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger("orchestration.plugins")


@dataclass
class PluginInfo:
    """Plugin information"""
    name: str
    version: str
    description: str
    author: str
    hooks: List[str]


class Plugin:
    """Base plugin class"""
    
    name: str = "base"
    version: str = "1.0.0"
    description: str = ""
    hooks: List[str] = []
    
    def on_load(self):
        """Called when plugin is loaded"""
        pass
    
    def on_unload(self):
        """Called when plugin is unloaded"""
        pass
    
    def pre_process(self, data: Any) -> Any:
        """Pre-processing hook"""
        return data
    
    def post_process(self, data: Any) -> Any:
        """Post-processing hook"""
        return data


class PluginManager:
    """Plugin manager"""
    
    def __init__(self, plugin_dir: str = "./plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[Callable]] = {}
    
    def discover_plugins(self) -> List[PluginInfo]:
        """Discover available plugins"""
        if not self.plugin_dir.exists():
            return []
        
        plugins = []
        for py_file in self.plugin_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            # Would load and inspect plugin
            plugins.append(PluginInfo(
                name=py_file.stem,
                version="1.0.0",
                description="Discovered plugin",
                author="unknown",
                hooks=["pre_process", "post_process"],
            ))
        
        return plugins
    
    def load_plugin(self, name: str) -> bool:
        """Load a plugin"""
        try:
            # Dynamic import
            module = importlib.import_module(f"plugins.{name}")
            
            # Find plugin class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                    plugin = attr()
                    self.plugins[name] = plugin
                    plugin.on_load()
                    
                    # Register hooks
                    for hook in plugin.hooks:
                        if hook not in self.hooks:
                            self.hooks[hook] = []
                        self.hooks[hook].append(plugin)
                    
                    logger.info(f"Loaded plugin: {name}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")
        
        return False
    
    def unload_plugin(self, name: str):
        """Unload a plugin"""
        if name in self.plugins:
            self.plugins[name].on_unload()
            del self.plugins[name]
            
            # Remove hooks
            for hook_name in self.hooks:
                self.hooks[hook_name] = [
                    p for p in self.hooks[hook_name]
                    if p.name != name
                ]
    
    def execute_hook(self, hook_name: str, data: Any) -> Any:
        """Execute all hooks for a given hook name"""
        if hook_name not in self.hooks:
            return data
        
        for plugin in self.hooks[hook_name]:
            try:
                data = plugin.pre_process(data) if hook_name == "pre_process" else plugin.post_process(data)
            except Exception as e:
                logger.error(f"Hook {hook_name} failed for {plugin.name}: {e}")
        
        return data
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugins"""
        return list(self.plugins.keys())


# Example plugin
class ExamplePlugin(Plugin):
    """Example plugin for logging"""
    
    name = "example"
    version = "1.0.0"
    description = "Example plugin"
    hooks = ["pre_process", "post_process"]
    
    def pre_process(self, data: Any) -> Any:
        logger.info(f"Pre-process: {data}")
        return data
    
    def post_process(self, data: Any) -> Any:
        logger.info(f"Post-process: {data}")
        return data


# Plugin loader for setuptools
def get_plugins() -> Dict[str, type]:
    """Get available plugin classes"""
    return {
        "example": ExamplePlugin,
    }
