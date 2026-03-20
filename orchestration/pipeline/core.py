"""Pipeline utilities"""

from typing import Any, List, Callable


class Pipeline:
    """Simple pipeline"""
    
    def __init__(self):
        self.stages: List[Callable] = []
    
    def add(self, stage: Callable):
        self.stages.append(stage)
        return self
    
    def execute(self, data: Any) -> Any:
        result = data
        for stage in self.stages:
            result = stage(result)
        return result
