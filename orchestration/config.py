"""Configuration management"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("orchestration.config")


@dataclass
class DAGConfig:
    """DAG execution config"""
    max_workers: int = 4
    max_depth: int = 10
    chunk_size: int = 100
    timeout: int = 300
    retry_attempts: int = 3
    
    def to_dict(self) -> Dict:
        return {
            "max_workers": self.max_workers,
            "max_depth": self.max_depth,
            "chunk_size": self.chunk_size,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
        }


@dataclass 
class AgentConfig:
    """Agent config"""
    id: str
    name: str
    capabilities: list = field(default_factory=list)
    max_concurrent_tasks: int = 1


class ConfigManager:
    """Manage configuration"""
    
    def __init__(self):
        self.config = DAGConfig()
        self.agents = []
    
    def load_from_env(self):
        """Load from environment"""
        self.config.max_workers = int(os.getenv("DAG_MAX_WORKERS", "4"))
        self.config.max_depth = int(os.getenv("DAG_MAX_DEPTH", "10"))
        self.config.chunk_size = int(os.getenv("DAG_CHUNK_SIZE", "100"))
        self.config.timeout = int(os.getenv("DAG_TIMEOUT", "300"))
    
    def load_from_file(self, path: str):
        """Load from JSON file"""
        with open(path) as f:
            data = json.load(f)
        
        if "dag" in data:
            for key, value in data["dag"].items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
    
    def get(self) -> DAGConfig:
        return self.config
    
    def set(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)


_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get config manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager