"""Pipeline stages"""

import logging
from typing import List, Callable, Any

logger = logging.getLogger("orchestration.stages")


class Stage:
    """Pipeline stage"""
    
    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.handler = handler
    
    def execute(self, data: Any) -> Any:
        return self.handler(data)


class StagePipeline:
    """Pipeline of stages"""
    
    def __init__(self):
        self.stages: List[Stage] = []
    
    def add(self, name: str, handler: Callable) -> "StagePipeline":
        self.stages.append(Stage(name, handler))
        return self
    
    def execute(self, data: Any) -> Any:
        result = data
        for stage in self.stages:
            result = stage.execute(result)
        return result
