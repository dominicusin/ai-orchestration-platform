"""Pipeline loaders for configuration"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("orchestration.loaders")


class Loader:
    """Base loader"""
    
    def load(self, source: str) -> Dict:
        raise NotImplementedError


class JSONLoader(Loader):
    """Load JSON configuration"""
    
    def load(self, source: str) -> Dict:
        path = Path(source)
        if not path.exists():
            return {}
        return json.loads(path.read_text())


class EnvLoader(Loader):
    """Load from environment"""
    
    def load(self, prefix: str = "") -> Dict:
        result = {}
        import os
        
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            
            clean_key = key[len(prefix):] if prefix else key
            result[clean_key.lower()] = value
        
        return result


class LoaderFactory:
    """Create loaders"""
    
    @staticmethod
    def create(format: str) -> Loader:
        if format == "json":
            return JSONLoader()
        elif format == "env":
            return EnvLoader()
        raise ValueError(f"Unknown format: {format}")


def load_config(source: str, format: str = "json") -> Dict:
    """Load configuration"""
    loader = LoaderFactory.create(format)
    return loader.load(source)
