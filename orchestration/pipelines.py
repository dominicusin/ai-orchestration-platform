"""Pipeline pipelines for chaining operations"""

import logging
from typing import Any, Callable, List

logger = logging.getLogger("orchestration.pipelines")


class Pipeline:
    """Data pipeline"""
    
    def __init__(self, name: str = "pipeline"):
        self.name = name
        self.steps: List[Callable] = []
    
    def add(self, step: Callable) -> "Pipeline":
        self.steps.append(step)
        return self
    
    def execute(self, data: Any) -> Any:
        result = data
        for step in self.steps:
            result = step(result)
        return result
    
    async def execute_async(self, data: Any) -> Any:
        import asyncio
        result = data
        for step in self.steps:
            if asyncio.iscoroutinefunction(step):
                result = await step(result)
            else:
                result = step(result)
        return result


def create_pipeline(name: str = "pipeline") -> Pipeline:
    """Create pipeline"""
    return Pipeline(name)


# Predefined pipelines
def create_analysis_pipeline() -> Pipeline:
    """Create analysis pipeline"""
    return Pipeline("analysis").add(lambda x: x)


def create_conversion_pipeline() -> Pipeline:
    """Create conversion pipeline"""
    return Pipeline("conversion").add(lambda x: x)


def create_export_pipeline() -> Pipeline:
    """Create export pipeline"""
    return Pipeline("export").add(lambda x: x)
