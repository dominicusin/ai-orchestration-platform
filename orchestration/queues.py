"""Pipeline queues"""

import asyncio
import logging
from typing import Any, Optional
from collections import deque

logger = logging.getLogger("orchestration.queues")


class Queue:
    """Base queue"""
    
    def enqueue(self, item: Any):
        raise NotImplementedError
    
    def dequeue(self) -> Optional[Any]:
        raise NotImplementedError
    
    def is_empty(self) -> bool:
        raise NotImplementedError


class InMemoryQueue(Queue):
    """In-memory queue"""
    
    def __init__(self):
        self.items = deque()
    
    def enqueue(self, item: Any):
        self.items.append(item)
    
    def dequeue(self) -> Optional[Any]:
        if self.items:
            return self.items.popleft()
        return None
    
    def is_empty(self) -> bool:
        return len(self.items) == 0


class PriorityQueue(Queue):
    """Priority queue"""
    
    def __init__(self):
        self.items = []
    
    def enqueue(self, item: Any, priority: int = 0):
        self.items.append((priority, item))
        self.items.sort(key=lambda x: x[0])
    
    def dequeue(self) -> Optional[Any]:
        if self.items:
            return self.items.pop(0)[1]
        return None
    
    def is_empty(self) -> bool:
        return len(self.items) == 0
