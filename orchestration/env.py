"""Environment utilities"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger("orchestration.env")


@dataclass
class EnvConfig:
    """Environment configuration"""
    # AI
    default_provider: str = "ollama"
    ollama_model: str = "gemma3:1b"
    groq_api_key: str = ""
    
    # Paths
    project_path: str = "./OpenPapyrus"
    output_path: str = "./Surypus2"
    
    # Processing
    max_workers: int = 4
    batch_size: int = 10
    
    # Cache
    cache_policy: str = "memory"
    redis_url: str = ""
    
    # Logging
    log_format: str = "text"
    log_level: str = "INFO"
    
    # Monitoring
    enable_prometheus: bool = True
    prometheus_port: int = 9090
    
    # Features
    enable_rlm: bool = False
    auto_commit: bool = False


def load_env_file(path: str = ".env") -> Dict[str, str]:
    """Load .env file"""
    env_vars = {}
    
    env_path = Path(path)
    if not env_path.exists():
        return env_vars
    
    for line in env_path.read_text().splitlines():
        line = line.strip()
        
        if not line or line.startswith("#"):
            continue
        
        if "=" in line:
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip()
    
    return env_vars


def get_env(key: str, default: Any = None, required: bool = False) -> Any:
    """Get environment variable"""
    value = os.getenv(key, default)
    
    if required and value is None:
        logger.warning(f"Required env var not set: {key}")
    
    return value


def get_bool_env(key: str, default: bool = False) -> bool:
    """Get boolean environment variable"""
    value = os.getenv(key, "").lower()
    
    if value in ("true", "1", "yes", "on"):
        return True
    elif value in ("false", "0", "no", "off"):
        return False
    
    return default


def get_int_env(key: str, default: int = 0) -> int:
    """Get integer environment variable"""
    value = os.getenv(key)
    
    if value:
        try:
            return int(value)
        except ValueError:
            pass
    
    return default


def set_env_if_missing(key: str, value: str):
    """Set env var if not already set"""
    if key not in os.environ:
        os.environ[key] = value


def get_all_env(prefix: str = "") -> Dict[str, str]:
    """Get all environment variables with prefix"""
    if prefix:
        prefix = prefix.upper() + "_"
    
    return {
        key: value
        for key, value in os.environ.items()
        if key.startswith(prefix)
    }


def validate_required_envs() -> Dict[str, Any]:
    """Validate required environment variables"""
    required = []
    warnings = []
    
    # Check provider API keys
    provider = get_env("DEFAULT_PROVIDER", "ollama")
    
    if provider == "groq" and not get_env("GROQ_API_KEY"):
        required.append("GROQ_API_KEY")
    
    if provider == "openai" and not get_env("OPENAI_API_KEY"):
        required.append("OPENAI_API_KEY")
    
    if provider == "anthropic" and not get_env("ANTHROPIC_API_KEY"):
        required.append("ANTHROPIC_API_KEY")
    
    # Check paths
    project_path = get_env("PROJECT_PATH", "./OpenPapyrus")
    if not Path(project_path).exists():
        warnings.append(f"Project path does not exist: {project_path}")
    
    return {
        "valid": len(required) == 0,
        "required": required,
        "warnings": warnings,
    }
