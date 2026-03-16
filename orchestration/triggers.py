"""Pipeline triggers"""

import time
import logging
from typing import Dict, Any, List, Callable
from dataclasses import dataclass

logger = logging.getLogger("orchestration.triggers")


@dataclass
class Trigger:
    """Pipeline trigger"""
    name: str
    condition: Callable[[Dict], bool]
    action: Callable


class TriggerManager:
    """Manage pipeline triggers"""
    
    def __init__(self):
        self.triggers: List[Trigger] = []
    
    def add(self, trigger: Trigger):
        self.triggers.append(trigger)
    
    def evaluate(self, context: Dict) -> List[Trigger]:
        """Evaluate triggers"""
        active = []
        
        for trigger in self.triggers:
            if trigger.condition(context):
                active.append(trigger)
        
        return active
    
    def execute(self, context: Dict):
        """Execute active triggers"""
        for trigger in self.evaluate(context):
            trigger.action(context)


def file_changed_trigger(path: str) -> Callable:
    """Create file changed trigger"""
    def condition(context: Dict) -> bool:
        return context.get("file") == path
    return condition


def size_trigger(min_size: int) -> Callable:
    """Create size trigger"""
    def condition(context: Dict) -> bool:
        return context.get("size", 0) > min_size
    return condition
