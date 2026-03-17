"""Pipeline sources"""

import logging
from typing import Any, List

logger = logging.getLogger("orchestration.sources")


class Source:
    """Base source"""
    
    def read(self) -> Any:
        raise NotImplementedError


class ListSource(Source):
    """List source"""
    
    def __init__(self, items: List):
        self.items = iter(items)
    
    def read(self) -> Any:
        try:
            return next(self.items)
        except StopIteration:
            return None


class DictSource(Source):
    """Dictionary source"""
    
    def __init__(self, data: dict):
        self.data = data
        self.keys = iter(data.keys())
    
    def read(self) -> Any:
        try:
            key = next(self.keys)
            return {key: self.data[key]}
        except StopIteration:
            return None


class RepeatSource(Source):
    """Repeat single value"""
    
    def __init__(self, value: Any):
        self.value = value
    
    def read(self) -> Any:
        return self.value
