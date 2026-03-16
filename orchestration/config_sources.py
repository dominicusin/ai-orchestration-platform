"""Pipeline configuration sources"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("orchestration.config_sources")


class ConfigSource:
    """Base config source"""
    
    def load(self) -> Dict:
        raise NotImplementedError


class DictSource(ConfigSource):
    """Dictionary config source"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def load(self) -> Dict:
        return self.config


class MultiSource(ConfigSource):
    """Multiple config sources"""
    
    def __init__(self, sources: List[ConfigSource]):
        self.sources = sources
    
    def load(self) -> Dict:
        result = {}
        for source in self.sources:
            result.update(source.load())
        return result


def merge_configs(*configs: Dict) -> Dict:
    """Merge multiple configs"""
    result = {}
    for config in configs:
        result.update(config)
    return result
