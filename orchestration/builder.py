"""Pipeline builder for fluent configuration"""

import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("orchestration.builder")


@dataclass
class PipelineStep:
    """Pipeline step"""
    name: str
    handler: Callable
    config: Dict = field(default_factory=dict)


class PipelineBuilder:
    """Build pipeline with fluent API"""
    
    def __init__(self, name: str = "pipeline"):
        self.name = name
        self.steps: List[PipelineStep] = []
        self.config: Dict[str, Any] = {}
    
    def with_config(self, **kwargs) -> "PipelineBuilder":
        """Add configuration"""
        self.config.update(kwargs)
        return self
    
    def with_step(self, name: str, handler: Callable, **config) -> "PipelineBuilder":
        """Add step"""
        self.steps.append(PipelineStep(name, handler, config))
        return self
    
    def with_analyze(self, handler: Callable) -> "PipelineBuilder":
        """Add analyze step"""
        return self.with_step("analyze", handler)
    
    def with_database(self, handler: Callable) -> "PipelineBuilder":
        """Add database step"""
        return self.with_step("database", handler)
    
    def with_haskell(self, handler: Callable) -> "PipelineBuilder":
        """Add haskell step"""
        return self.with_step("haskell", handler)
    
    def with_qml(self, handler: Callable) -> "PipelineBuilder":
        """Add qml step"""
        return self.with_step("qml", handler)
    
    def with_reports(self, handler: Callable) -> "PipelineBuilder":
        """Add reports step"""
        return self.with_step("reports", handler)
    
    def build(self):
        """Build pipeline"""
        return {
            "name": self.name,
            "config": self.config,
            "steps": [
                {"name": s.name, "config": s.config}
                for s in self.steps
            ],
        }


def create_pipeline(name: str = "pipeline") -> PipelineBuilder:
    """Create pipeline builder"""
    return PipelineBuilder(name)
