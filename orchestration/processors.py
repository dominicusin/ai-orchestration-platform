"""Pipeline processors"""

import logging
from typing import Any, Dict

logger = logging.getLogger("orchestration.processors")


class Processor:
    """Base processor"""
    
    def process(self, data: Any) -> Any:
        raise NotImplementedError


class MapProcessor(Processor):
    """Map processor"""
    
    def __init__(self, func):
        self.func = func
    
    def process(self, data: Any) -> Any:
        return self.func(data)


class FilterProcessor(Processor):
    """Filter processor"""
    
    def __init__(self, predicate):
        self.predicate = predicate
    
    def process(self, data: Any) -> Any:
        return [item for item in data if self.predicate(item)]


class FlatMapProcessor(Processor):
    """FlatMap processor"""
    
    def __init__(self, func):
        self.func = func
    
    def process(self, data: Any) -> Any:
        result = []
        for item in data:
            result.extend(self.func(item))
        return result
