"""Configuration management with validation"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("orchestration.config")


class LogFormat(Enum):
    TEXT = "text"
    JSON = "json"


class CachePolicy(Enum):
    MEMORY = "memory"
    DISK = "disk"
    NONE = "none"


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    # Paths
    project_path: str = "./OpenPapyrus"
    output_path: str = "./Surypus2"
    
    # Processing
    max_workers: int = 4
    batch_size: int = 10
    
    # AI
    default_provider: str = "ollama"
    ollama_model: str = "gemma3:1b"
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Cache
    cache_policy: str = "memory"
    max_memory_cache: int = 1000
    
    # Logging
    log_format: str = "text"
    log_level: str = "INFO"
    
    # Monitoring
    enable_prometheus: bool = True
    prometheus_port: int = 9090
    
    # RLM
    enable_rlm: bool = False
    rlm_max_depth: int = 2
    rlm_use_infiniretri: bool = False
    
    # Validation
    validate_haskell: bool = True
    validate_qml: bool = True
    validate_sql: bool = True
    
    # Advanced
    retry_attempts: int = 3
    timeout_seconds: int = 300


class ConfigManager:
    """Configuration manager"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.getenv("PIPELINE_CONFIG", ".pipeline.json")
        self.config = PipelineConfig()
        self._load()
    
    def _load(self):
        """Load configuration from file and environment"""
        # Load from file if exists
        path = Path(self.config_file)
        if path.exists():
            try:
                data = json.loads(path.read_text())
                self._apply_dict(data)
                logger.info(f"Loaded config from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        # Override with environment variables
        self._load_env()
    
    def _apply_dict(self, data: Dict[str, Any]):
        """Apply dictionary to config"""
        for key, value in data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def _load_env(self):
        """Load from environment variables"""
        env_mappings = {
            "PROJECT_PATH": "project_path",
            "OUTPUT_PATH": "output_path",
            "MAX_WORKERS": "max_workers",
            "BATCH_SIZE": "batch_size",
            "DEFAULT_PROVIDER": "default_provider",
            "OLLAMA_MODEL": "ollama_model",
            "GROQ_MODEL": "groq_model",
            "CACHE_POLICY": "cache_policy",
            "LOG_FORMAT": "log_format",
            "LOG_LEVEL": "log_level",
            "ENABLE_PROMETHEUS": "enable_prometheus",
            "PROMETHEUS_PORT": "prometheus_port",
            "ENABLE_RLM": "enable_rlm",
            "RLM_MAX_DEPTH": "rlm_max_depth",
            "VALIDATE_HASKELL": "validate_haskell",
            "VALIDATE_QML": "validate_qml",
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion
                if isinstance(getattr(self.config, config_key), bool):
                    value = value.lower() in ("true", "1", "yes")
                elif isinstance(getattr(self.config, config_key), int):
                    value = int(value)
                
                setattr(self.config, config_key, value)
    
    def save(self, path: str = None):
        """Save configuration"""
        path = path or self.config_file
        data = {
            "project_path": self.config.project_path,
            "output_path": self.config.output_path,
            "max_workers": self.config.max_workers,
            "default_provider": self.config.default_provider,
            "ollama_model": self.config.ollama_model,
            "cache_policy": self.config.cache_policy,
            "log_format": self.config.log_format,
            "enable_prometheus": self.config.enable_prometheus,
            "enable_rlm": self.config.enable_rlm,
        }
        
        Path(path).write_text(json.dumps(data, indent=2))
        logger.info(f"Config saved to {path}")
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration"""
        errors = []
        warnings = []
        
        # Check paths exist
        if not Path(self.config.project_path).exists():
            errors.append(f"Project path does not exist: {self.config.project_path}")
        
        # Check workers
        if self.config.max_workers < 1:
            warnings.append("max_workers should be >= 1")
        
        # Check provider
        valid_providers = ["ollama", "groq", "deepseek", "mistral", "anthropic", "google"]
        if self.config.default_provider not in valid_providers:
            warnings.append(f"Unknown provider: {self.config.default_provider}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "project_path": self.config.project_path,
            "output_path": self.config.output_path,
            "max_workers": self.config.max_workers,
            "default_provider": self.config.default_provider,
            "ollama_model": self.config.ollama_model,
            "log_format": self.config.log_format,
            "enable_prometheus": self.config.enable_prometheus,
            "enable_rlm": self.config.enable_rlm,
        }


# Global config instance
_config: Optional[PipelineConfig] = None


def get_config() -> PipelineConfig:
    """Get global config"""
    global _config
    if _config is None:
        manager = ConfigManager()
        _config = manager.config
    return _config


def init_config(**kwargs) -> PipelineConfig:
    """Initialize config with overrides"""
    global _config
    
    manager = ConfigManager()
    for key, value in kwargs.items():
        if hasattr(manager.config, key):
            setattr(manager.config, key, value)
    
    _config = manager.config
    return _config


# Example config file
EXAMPLE_CONFIG = """{
    "project_path": "./OpenPapyrus",
    "output_path": "./Surypus2",
    "max_workers": 4,
    "default_provider": "ollama",
    "ollama_model": "gemma3:1b",
    "cache_policy": "memory",
    "log_format": "json",
    "log_level": "INFO",
    "enable_prometheus": true,
    "prometheus_port": 9090,
    "enable_rlm": false,
    "validate_haskell": true,
    "validate_qml": true,
    "retry_attempts": 3,
    "timeout_seconds": 300
}
"""


if __name__ == "__main__":
    # Demo
    config = get_config()
    print(f"Project: {config.project_path}")
    print(f"Provider: {config.default_provider}")
    print(f"Workers: {config.max_workers}")
    
    # Validate
    manager = ConfigManager()
    result = manager.validate()
    print(f"Valid: {result['valid']}")
    if result['warnings']:
        print(f"Warnings: {result['warnings']}")
