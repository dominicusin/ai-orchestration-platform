"""Data models for DAG execution"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ExecutionModel:
    """Execution model"""
    id: str
    name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "created"
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskModel:
    """Task model"""
    id: str
    name: str
    task_type: str
    handler: str = ""
    args: list = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    result: Any = None


@dataclass
class AgentModel:
    """Agent model"""
    id: str
    name: str
    capabilities: list[str] = field(default_factory=list)
    status: str = "idle"
    current_task: str | None = None


@dataclass
class ResultModel:
    """Result model"""
    task_id: str
    success: bool
    output: Any = None
    error: str | None = None
    duration: float = 0
