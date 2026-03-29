"""Pipeline context and shared state"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("orchestration.context")


@dataclass
class PipelineContext:
    """Shared pipeline context"""
    project_path: str = ""
    output_path: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get(self, key: str, default: Any = None) -> Any:
        """Get value"""
        return self.state.get(key, default)

    def set(self, key: str, value: Any):
        """Set value"""
        self.state[key] = value

    def update(self, data: dict):
        """Update multiple values"""
        self.state.update(data)

    def to_dict(self) -> dict:
        """Convert to dict"""
        return {
            "project_path": self.project_path,
            "output_path": self.output_path,
            "config": self.config,
            "state": self.state,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class ContextManager:
    """Manage pipeline contexts"""

    def __init__(self):
        self.contexts: dict[str, PipelineContext] = {}

    def create(self, project_id: str, **kwargs) -> PipelineContext:
        """Create context"""
        ctx = PipelineContext(**kwargs)
        self.contexts[project_id] = ctx
        return ctx

    def get(self, project_id: str) -> PipelineContext | None:
        """Get context"""
        return self.contexts.get(project_id)

    def delete(self, project_id: str):
        """Delete context"""
        if project_id in self.contexts:
            del self.contexts[project_id]

    def list_contexts(self) -> list:
        """List all contexts"""
        return list(self.contexts.keys())


# Global manager
_context_manager: ContextManager | None = None


def get_context_manager() -> ContextManager:
    """Get context manager"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
