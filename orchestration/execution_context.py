"""Pipeline execution context"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("orchestration.execution_context")


class ExecutionContext:
    """Execution context"""
    
    def __init__(self, data: Dict = None):
        self.data = data or {}
        self.metadata = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        self.data[key] = value
    
    def has(self, key: str) -> bool:
        return key in self.data
    
    def clear(self):
        self.data = {}


class ContextStack:
    """Stack of contexts"""
    
    def __init__(self):
        self.stack = []
    
    def push(self, context: ExecutionContext):
        self.stack.append(context)
    
    def pop(self) -> ExecutionContext:
        if self.stack:
            return self.stack.pop()
        return ExecutionContext()
    
    def current(self) -> ExecutionContext:
        if self.stack:
            return self.stack[-1]
        return ExecutionContext()
