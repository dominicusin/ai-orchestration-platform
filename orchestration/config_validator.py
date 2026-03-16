"""Configuration validator"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("orchestration.config_validator")


class ValidationLevel(Enum):
    """Validation level"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Validation issue"""
    level: str
    field: str
    message: str
    suggestion: Optional[str] = None


class ConfigValidator:
    """Validate pipeline configuration"""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
    
    def validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration"""
        self.issues = []
        
        # Required fields
        self._check_required(config)
        
        # Paths
        self._check_paths(config)
        
        # AI settings
        self._check_ai(config)
        
        # Processing settings
        self._check_processing(config)
        
        # Cache settings
        self._check_cache(config)
        
        # Monitoring
        self._check_monitoring(config)
        
        return {
            "valid": not any(i.level == ValidationLevel.ERROR.value for i in self.issues),
            "issues": [
                {
                    "level": i.level,
                    "field": i.field,
                    "message": i.message,
                    "suggestion": i.suggestion,
                }
                for i in self.issues
            ],
        }
    
    def _add_issue(self, level: ValidationLevel, field: str, message: str, suggestion: str = None):
        """Add validation issue"""
        self.issues.append(ValidationIssue(
            level=level.value,
            field=field,
            message=message,
            suggestion=suggestion,
        ))
    
    def _check_required(self, config: Dict):
        """Check required fields"""
        required = ["project_path", "output_path"]
        
        for field in required:
            if field not in config or not config[field]:
                self._add_issue(
                    ValidationLevel.ERROR,
                    field,
                    f"Required field '{field}' is missing",
                    f"Set {field} in config or environment",
                )
    
    def _check_paths(self, config: Dict):
        """Check path settings"""
        project_path = config.get("project_path")
        
        if project_path and not Path(project_path).exists():
            self._add_issue(
                ValidationLevel.WARNING,
                "project_path",
                f"Project path does not exist: {project_path}",
                "Create the directory or update project_path",
            )
        
        output_path = config.get("output_path")
        if output_path:
            output_dir = Path(output_path)
            if output_dir.exists() and not os.access(output_dir, os.W_OK):
                self._add_issue(
                    ValidationLevel.ERROR,
                    "output_path",
                    f"Output path is not writable: {output_path}",
                    "Check directory permissions",
                )
    
    def _check_ai(self, config: Dict):
        """Check AI settings"""
        provider = config.get("default_provider")
        
        # Check if provider is set
        if not provider:
            self._add_issue(
                ValidationLevel.WARNING,
                "default_provider",
                "No AI provider configured",
                "Set DEFAULT_PROVIDER environment variable",
            )
        
        # Check provider-specific settings
        if provider == "ollama":
            if not os.getenv("OLLAMA_MODEL"):
                self._add_issue(
                    ValidationLevel.INFO,
                    "ollama_model",
                    "No Ollama model specified",
                    "Set OLLAMA_MODEL (e.g., gemma3:1b)",
                )
        
        elif provider == "groq":
            if not os.getenv("GROQ_API_KEY"):
                self._add_issue(
                    ValidationLevel.ERROR,
                    "groq_api_key",
                    "GROQ_API_KEY not set",
                    "Set GROQ_API_KEY environment variable",
                )
    
    def _check_processing(self, config: Dict):
        """Check processing settings"""
        max_workers = config.get("max_workers", 4)
        
        if max_workers < 1:
            self._add_issue(
                ValidationLevel.ERROR,
                "max_workers",
                "max_workers must be at least 1",
                "Set max_workers to a positive number",
            )
        elif max_workers > 32:
            self._add_issue(
                ValidationLevel.WARNING,
                "max_workers",
                f"High worker count: {max_workers}",
                "Consider using 8-16 workers for stability",
            )
        
        batch_size = config.get("batch_size", 10)
        if batch_size < 1:
            self._add_issue(
                ValidationLevel.ERROR,
                "batch_size",
                "batch_size must be at least 1",
            )
    
    def _check_cache(self, config: Dict):
        """Check cache settings"""
        cache_policy = config.get("cache_policy", "memory")
        
        if cache_policy not in ["memory", "disk", "none"]:
            self._add_issue(
                ValidationLevel.ERROR,
                "cache_policy",
                f"Invalid cache policy: {cache_policy}",
                "Use 'memory', 'disk', or 'none'",
            )
    
    def _check_monitoring(self, config: Dict):
        """Check monitoring settings"""
        if config.get("enable_prometheus"):
            port = config.get("prometheus_port", 9090)
            
            if port < 1024 or port > 65535:
                self._add_issue(
                    ValidationLevel.WARNING,
                    "prometheus_port",
                    f"Port {port} is outside recommended range",
                    "Use a port between 1024 and 65535",
                )


def validate_config(config: Dict) -> Dict:
    """Validate configuration"""
    validator = ConfigValidator()
    return validator.validate(config)


def validate_env() -> Dict:
    """Validate environment configuration"""
    config = {
        "project_path": os.getenv("PROJECT_PATH", "./OpenPapyrus"),
        "output_path": os.getenv("OUTPUT_PATH", "./Surypus2"),
        "max_workers": int(os.getenv("MAX_WORKERS", "4")),
        "default_provider": os.getenv("DEFAULT_PROVIDER"),
        "cache_policy": os.getenv("CACHE_POLICY", "memory"),
        "log_format": os.getenv("LOG_FORMAT", "text"),
        "enable_prometheus": os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true",
        "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "9090")),
    }
    
    return validate_config(config)
