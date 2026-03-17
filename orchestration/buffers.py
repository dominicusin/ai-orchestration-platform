"""Pipeline buffers"""

import logging
from typing import Any, List

logger = logging.getLogger("orchestration.buffers")
    """Base buffer"""
    
    def write(self, item: Any):
        raise NotImplementedError
    
    def read(self) -> Any:
        raise NotImplementedError
    
    def is_empty(self) -> bool:
        raise NotImplementedError
    
    def is_full(self) -> bool:
        raise NotImplementedError


class RingBuffer(Buffer):
    """Ring buffer"""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = [None] * capacity
        self.head = 0
        self.tail = 0
        self.size = 0
    
    def write(self, item: Any):
        self.buffer[self.tail] = item
        self.tail = (self.tail + 1) % self.capacity
        if self.size < self.capacity:
            self.size += 1
        elif self.head != self.tail:
            self.head = (self.head + 1) % self.capacity
    
    def read(self) -> Any:
        if self.size == 0:
            return None
        item = self.buffer[self.head]
        self.head = (self.head + 1) % self.capacity
        self.size -= 1
        return item
    
    def is_empty(self) -> bool:
        return self.size == 0
    
    def is_full(self) -> bool:
        return self.size == self.capacity
