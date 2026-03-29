"""Pipeline utilities"""

from collections.abc import Callable
from typing import Any


class Pipeline:
    """Simple pipeline"""

    def __init__(self):
        self.stages: list[Callable] = []

    def add(self, stage: Callable):
        self.stages.append(stage)
        return self

    def execute(self, data: Any) -> Any:
        result = data
        for stage in self.stages:
            result = stage(result)
        return result
