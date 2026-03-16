"""Event system for pipeline hooks and triggers"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger("orchestration.events")


class EventType(Enum):
    """Event types"""
    # Pipeline events
    PIPELINE_START = "pipeline.start"
    PIPELINE_COMPLETE = "pipeline.complete"
    PIPELINE_ERROR = "pipeline.error"
    PIPELINE_CANCEL = "pipeline.cancel"
    
    # Phase events
    PHASE_START = "phase.start"
    PHASE_PROGRESS = "phase.progress"
    PHASE_COMPLETE = "phase.complete"
    PHASE_ERROR = "phase.error"
    
    # File events
    FILE_DISCOVERED = "file.discovered"
    FILE_PROCESSING = "file.processing"
    FILE_CONVERTED = "file.converted"
    FILE_FAILED = "file.failed"
    FILE_VALIDATED = "file.validated"
    
    # AI events
    AI_CALL_START = "ai.call.start"
    AI_CALL_COMPLETE = "ai.call.complete"
    AI_CALL_ERROR = "ai.call.error"
    AI_RATE_LIMIT = "ai.rate_limit"
    
    # Cache events
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    CACHE_CLEAR = "cache.clear"


@dataclass
class Event:
    """Event"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "pipeline"
    correlation_id: Optional[str] = None


class EventListener:
    """Event listener/callback"""
    
    def __init__(
        self,
        event_type: str,
        callback: Callable,
        name: str = None,
        once: bool = False,
    ):
        self.event_type = event_type
        self.callback = callback
        self.name = name or callback.__name__
        self.once = once


class EventBus:
    """Event bus for publish-subscribe"""
    
    def __init__(self):
        self.listeners: Dict[str, List[EventListener]] = {}
        self.event_history: List[Event] = []
        self.max_history = 1000
    
    def subscribe(
        self,
        event_type: str,
        callback: Callable,
        name: str = None,
        once: bool = False,
    ) -> EventListener:
        """Subscribe to an event"""
        listener = EventListener(event_type, callback, name, once)
        
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        
        self.listeners[event_type].append(listener)
        
        logger.debug(f"Subscribed to {event_type}: {listener.name}")
        
        return listener
    
    def unsubscribe(self, event_type: str, name: str = None):
        """Unsubscribe from an event"""
        if event_type not in self.listeners:
            return
        
        if name:
            self.listeners[event_type] = [
                l for l in self.listeners[event_type]
                if l.name != name
            ]
        else:
            self.listeners[event_type] = []
    
    def subscribe_all(self, callback: Callable, name: str = None):
        """Subscribe to all events"""
        for event_type in EventType:
            self.subscribe(event_type.value, callback, name)
    
    async def publish(self, event: Event):
        """Publish an event"""
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Get listeners
        listeners = self.listeners.get(event.type, [])
        
        # Also check wildcard listeners
        listeners += self.listeners.get("*", [])
        
        # Call listeners
        for listener in list(listeners):
            try:
                if asyncio.iscoroutinefunction(listener.callback):
                    await listener.callback(event)
                else:
                    listener.callback(event)
                
                if listener.once:
                    self.listeners[event.type].remove(listener)
                    
            except Exception as e:
                logger.error(f"Event listener error: {listener.name} - {e}")
    
    def publish_sync(self, event: Event):
        """Synchronous publish (for non-async contexts)"""
        # Store in history
        self.event_history.append(event)
        
        # Get listeners
        listeners = self.listeners.get(event.type, [])
        listeners += self.listeners.get("*", [])
        
        # Call listeners
        for listener in list(listeners):
            try:
                listener.callback(event)
            except Exception as e:
                logger.error(f"Event listener error: {listener.name} - {e}")
    
    def get_history(
        self,
        event_type: str = None,
        limit: int = 100,
    ) -> List[Event]:
        """Get event history"""
        if event_type:
            return [
                e for e in self.event_history
                if e.type == event_type
            ][:limit]
        
        return self.event_history[:limit]
    
    def clear_history(self):
        """Clear event history"""
        self.event_history = []


class Trigger:
    """Event trigger"""
    
    def __init__(
        self,
        name: str,
        event_type: str,
        condition: Callable[[Event], bool],
        action: Callable,
    ):
        self.name = name
        self.event_type = event_type
        self.condition = condition
        self.action = action
        self.enabled = True
    
    async def check_and_execute(self, event: Event):
        """Check condition and execute action"""
        if not self.enabled:
            return
        
        if self.event_type != event.type:
            return
        
        try:
            if self.condition(event):
                logger.info(f"Trigger fired: {self.name}")
                
                if asyncio.iscoroutinefunction(self.action):
                    await self.action(event)
                else:
                    self.action(event)
                    
        except Exception as e:
            logger.error(f"Trigger error: {self.name} - {e}")


class TriggerManager:
    """Manage event triggers"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.triggers: List[Trigger] = []
    
    def add_trigger(self, trigger: Trigger):
        """Add a trigger"""
        self.triggers.append(trigger)
        logger.info(f"Added trigger: {trigger.name}")
    
    def remove_trigger(self, name: str):
        """Remove a trigger"""
        self.triggers = [t for t in self.triggers if t.name != name]
    
    async def process_event(self, event: Event):
        """Process event through triggers"""
        for trigger in self.triggers:
            await trigger.check_and_execute(event)
    
    def create_trigger(
        self,
        name: str,
        event_type: str,
        condition_json: str,
        action: Callable,
    ):
        """Create a trigger from config"""
        # Simple condition parser
        def parse_condition(event: Event) -> bool:
            # Simple equality check
            parts = condition_json.split("=")
            if len(parts) == 2:
                key, value = parts
                return event.data.get(key.strip()) == value.strip()
            return True
        
        trigger = Trigger(
            name=name,
            event_type=event_type,
            condition=parse_condition,
            action=action,
        )
        
        self.add_trigger(trigger)


# Event helpers
def create_event(event_type: EventType, data: Dict = None, source: str = "pipeline") -> Event:
    """Create an event"""
    return Event(
        type=event_type.value,
        data=data or {},
        source=source,
    )


# Global event bus
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global event bus"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Example usage
async def example_usage():
    """Example of using the event system"""
    bus = get_event_bus()
    
    # Subscribe to events
    async def on_pipeline_complete(event: Event):
        print(f"Pipeline completed: {event.data}")
    
    bus.subscribe(EventType.PIPELINE_COMPLETE.value, on_pipeline_complete)
    
    # Publish event
    event = create_event(
        EventType.PIPELINE_COMPLETE,
        {"runtime": 100, "files": 53}
    )
    await bus.publish(event)
    
    # Get history
    history = bus.get_history(EventType.PIPELINE_COMPLETE.value)
    print(f"Pipeline complete events: {len(history)}")
