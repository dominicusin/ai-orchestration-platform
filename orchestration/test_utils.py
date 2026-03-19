"""Test utilities"""

import asyncio
from typing import Any, Callable


def async_test(func: Callable) -> Callable:
    """Decorator for async tests"""
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


def create_mock_task(task_id: str = "test", handler: Callable = None):
    """Create mock task for testing"""
    from orchestration.graph_recursive import Task, TaskType
    
    return Task(
        id=task_id,
        name=task_id,
        task_type=TaskType.ATOMIC,
        handler=handler or (lambda: "result"),
    )


def create_mock_agent(agent_id: str = "test_agent", capabilities: list = None):
    """Create mock agent for testing"""
    from orchestration.graph_engine import Agent
    
    return Agent(
        id=agent_id,
        name=agent_id,
        capabilities=set(capabilities or ["code_execute"]),
    )


class MockExecutor:
    """Mock executor for testing"""
    
    def __init__(self):
        self.executed = []
    
    def execute(self, task):
        self.executed.append(task)
        return task.handler() if task.handler else None