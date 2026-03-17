"""Pipeline stacks"""

import logging
from typing import Any, Optional

logger = logging.getLogger("orchestration.stacks")


class Stack:
    """Base stack"""
    
    def push(self, item: Any):
        raise NotImplementedError
    
    def pop(self) -> Optional[Any]:
        raise NotImplementedError
    
    def peek(self) -> Optional[Any]:
        raise NotImplementedError
    
    def is_empty(self) -> bool:
        raise NotImplementedError


class InMemoryStack(Stack):
    """In-memory stack"""
    
    def __init__(self):
        self.items = []
    
    def push(self, item: Any):
        self.items.append(item)
    
    def pop(self) -> Optional[Any]:
        if self.items:
            return self.items.pop()
        return None
    
    def peek(self) -> Optional[Any]:
        if self.items:
            return self.items[-1]
        return None
    
    def is_empty(self) -> bool:
        return len(self.items) == 0


class UndoStack:
    """Stack for undo operations"""
    
    def __init__(self):
        self.stack = InMemoryStack()
        self.redo_stack = InMemoryStack()
    
    def execute(self, action, undo_action):
        self.stack.push((action, undo_action))
        self.redo_stack = InMemoryStack()
        return action()
    
    def undo(self):
        if self.stack.is_empty():
            return None
        action, undo_action = self.stack.pop()
        result = undo_action()
        self.redo_stack.push(action)
        return result
    
    def redo(self):
        if self.redo_stack.is_empty():
            return None
        action = self.redo_stack.pop()
        return action()
