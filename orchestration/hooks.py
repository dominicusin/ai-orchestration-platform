"""Hooks for DAG execution lifecycle"""

import logging
from typing import Callable, Any, List, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("orchestration.hooks")


class HookEvent(str, Enum):
    """Hook events"""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    LAYER_STARTED = "layer_started"
    LAYER_COMPLETED = "layer_completed"
    DAG_STARTED = "dag_started"
    DAG_COMPLETED = "dag_completed"


@dataclass
class HookContext:
    """Hook execution context"""
    event: HookEvent
    data: Any
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Hook:
    """Base hook"""
    
    def __init__(self, event: HookEvent, handler: Callable):
        self.event = event
        self.handler = handler
    
    def execute(self, context: HookContext):
        """Execute hook"""
        try:
            self.handler(context)
        except Exception as e:
            logger.error(f"Hook {self.event} failed: {e}")


class HookManager:
    """Manage execution hooks"""
    
    def __init__(self):
        self.hooks: Dict[HookEvent, List[Hook]] = {
            event: [] for event in HookEvent
        }
    
    def register(self, hook: Hook):
        """Register hook"""
        self.hooks[hook.event].append(hook)
        logger.info(f"Registered hook: {hook.event}")
    
    def on(self, event: HookEvent) -> Callable:
        """Decorator to register hook"""
        def decorator(handler: Callable) -> Callable:
            self.register(Hook(event, handler))
            return handler
        return decorator
    
    def trigger(self, event: HookEvent, data: Any = None, metadata: Dict = None):
        """Trigger all hooks for event"""
        context = HookContext(event, data, metadata)
        
        for hook in self.hooks[event]:
            hook.execute(context)


# Global hook manager
_hook_manager = None


def get_hook_manager() -> HookManager:
    """Get hook manager"""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager


# Example hooks
def log_task_started(context: HookContext):
    """Log task start"""
    logger.info(f"Task started: {context.data}")


def log_task_completed(context: HookContext):
    """Log task completion"""
    logger.info(f"Task completed: {context.data}")


def notify_on_failure(context: HookContext):
    """Notify on failure"""
    logger.warning(f"Task failed: {context.data}")