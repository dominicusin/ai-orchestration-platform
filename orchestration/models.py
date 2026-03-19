"""Data models for DAG execution"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class ExecutionModel:
    """Execution model"""
    id: str
    name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "created"
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskModel:
    """Task model"""
    id: str
    name: str
    task_type: str
    handler: str = ""
    args: List = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Any = None


@dataclass
class AgentModel:
    """Agent model"""
    id: str
    name: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "idle"
    current_task: Optional[str] = None


@dataclass
class ResultModel:
    """Result model"""
    task_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration: float = 0