"""Pipeline adapters for external systems"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("orchestration.adapters")


class Adapter:
    """Base adapter"""
    name: str = ""
    
    def connect(self) -> bool:
        """Connect to system"""
        raise NotImplementedError
    
    def disconnect(self):
        """Disconnect"""
        pass
    
    def execute(self, action: str, data: Dict) -> Any:
        """Execute action"""
        raise NotImplementedError


class FileSystemAdapter(Adapter):
    """File system adapter"""
    name = "filesystem"
    
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
    
    def connect(self) -> bool:
        return True
    
    def execute(self, action: str, data: Dict) -> Any:
        from pathlib import Path
        
        if action == "read":
            path = Path(self.base_path) / data["path"]
            return path.read_text()
        
        elif action == "write":
            path = Path(self.base_path) / data["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data["content"])
            return True
        
        elif action == "list":
            path = Path(self.base_path) / data.get("path", ".")
            return [str(p) for p in path.glob(data.get("pattern", "*"))]
        
        return None


class DatabaseAdapter(Adapter):
    """Database adapter"""
    name = "database"
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string
        self.connected = False
    
    def connect(self) -> bool:
        self.connected = True
        return True
    
    def execute(self, action: str, data: Dict) -> Any:
        if not self.connected:
            return None
        
        # Placeholder for actual DB operations
        return {"status": "ok"}


class CacheAdapter(Adapter):
    """Cache adapter"""
    name = "cache"
    
    def __init__(self):
        self.cache: Dict = {}
    
    def connect(self) -> bool:
        return True
    
    def execute(self, action: str, data: Dict) -> Any:
        if action == "get":
            return self.cache.get(data.get("key"))
        
        elif action == "set":
            self.cache[data["key"]] = data["value"]
            return True
        
        elif action == "delete":
            if data["key"] in self.cache:
                del self.cache[data["key"]]
            return True
        
        elif action == "clear":
            self.cache = {}
            return True
        
        return None


class AdapterManager:
    """Manage adapters"""
    
    def __init__(self):
        self.adapters: Dict[str, Adapter] = {}
    
    def register(self, adapter: Adapter):
        """Register adapter"""
        self.adapters[adapter.name] = adapter
        logger.info(f"Registered adapter: {adapter.name}")
    
    def get(self, name: str) -> Optional[Adapter]:
        """Get adapter"""
        return self.adapters.get(name)
    
    def connect_all(self):
        """Connect all adapters"""
        for adapter in self.adapters.values():
            adapter.connect()
    
    def disconnect_all(self):
        """Disconnect all adapters"""
        for adapter in self.adapters.values():
            adapter.disconnect()
