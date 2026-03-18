"""Event system for DAG execution"""

import asyncio
import logging
from typing import Callable, Dict, List, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger("orchestration.events")


class EventType(str, Enum):
    """Event types"""
    TASK_SUBMITTED = "task.submitted"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    LAYER_STARTED = "layer.started"
    LAYER_COMPLETED = "layer.completed"
    DAG_STARTED = "dag.started"
    DAG_COMPLETED = "dag.completed"
    WORKER_ASSIGNED = "worker.assigned"
    WORKER_RELEASED = "worker.released"


@dataclass
class Event:
    """Execution event"""
    id: str
    type: EventType
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class EventBus:
    """Event bus for pub/sub"""
    
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self.event_history: List[Event] = []
        self.max_history = 1000
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to event"""
        self.subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe from event"""
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
    
    def publish(self, event: Event):
        """Publish event"""
        self.event_history.append(event)
        
        # Trim history
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Notify subscribers
        for handler in self.subscribers.get(event.type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    def get_history(self, event_type: EventType = None, limit: int = 100) -> List[Event]:
        """Get event history"""
        if event_type:
            return [e for e in self.event_history if e.type == event_type][-limit:]
        return self.event_history[-limit:]


class EventEmitter:
    """Emit events during execution"""
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus or EventBus()
    
    def emit_task_submitted(self, task_id: str, layer: int):
        self.event_bus.publish(Event(
            type=EventType.TASK_SUBMITTED,
            data={"task_id": task_id, "layer": layer},
        ))
    
    def emit_task_started(self, task_id: str, worker_id: str):
        self.event_bus.publish(Event(
            type=EventType.TASK_STARTED,
            data={"task_id": task_id, "worker_id": worker_id},
        ))
    
    def emit_task_completed(self, task_id: str, duration: float):
        self.event_bus.publish(Event(
            type=EventType.TASK_COMPLETED,
            data={"task_id": task_id, "duration": duration},
        ))
    
    def emit_task_failed(self, task_id: str, error: str):
        self.event_bus.publish(Event(
            type=EventType.TASK_FAILED,
            data={"task_id": task_id, "error": error},
        ))
    
    def emit_layer_started(self, layer: int, task_count: int):
        self.event_bus.publish(Event(
            type=EventType.LAYER_STARTED,
            data={"layer": layer, "task_count": task_count},
        ))
    
    def emit_layer_completed(self, layer: int, completed: int, failed: int):
        self.event_bus.publish(Event(
            type=EventType.LAYER_COMPLETED,
            data={"layer": layer, "completed": completed, "failed": failed},
        ))
    
    def emit_dag_started(self, execution_id: str, total_tasks: int):
        self.event_bus.publish(Event(
            type=EventType.DAG_STARTED,
            data={"execution_id": execution_id, "total_tasks": total_tasks},
        ))
    
    def emit_dag_completed(self, execution_id: str, success: bool):
        self.event_bus.publish(Event(
            type=EventType.DAG_COMPLETED,
            data={"execution_id": execution_id, "success": success},
        ))


# Global event bus
_event_bus: EventBus = None


def get_event_bus() -> EventBus:
    """Get event bus"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def get_emitter() -> EventEmitter:
    """Get event emitter"""
    return EventEmitter(get_event_bus())