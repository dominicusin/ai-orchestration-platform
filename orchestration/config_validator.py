"""Configuration validator"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger("orchestration.config_validator")


class ConfigValidator:
    """Validate configuration"""
    
    def validate(self, config: Dict) -> List[str]:
        errors = []
        
        # Validate max_workers
        if "max_workers" in config:
            mw = config["max_workers"]
            if not isinstance(mw, int) or mw < 1 or mw > 100:
                errors.append("max_workers must be 1-100")
        
        # Validate timeout
        if "timeout" in config:
            to = config["timeout"]
            if not isinstance(to, int) or to < 1:
                errors.append("timeout must be positive")
        
        # Validate chunk_size
        if "chunk_size" in config:
            cs = config["chunk_size"]
            if not isinstance(cs, int) or cs < 1:
                errors.append("chunk_size must be positive")
        
        return errors
    
    def is_valid(self, config: Dict) -> bool:
        return len(self.validate(config)) == 0


def validate_config(config: Dict) -> bool:
    """Validate config"""
    return ConfigValidator().is_valid(config)