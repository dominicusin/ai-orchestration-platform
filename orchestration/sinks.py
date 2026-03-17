"""Pipeline sinks"""

import logging
from typing import Any, List

logger = logging.getLogger("orchestration.sinks")


class Sink:
    """Base sink"""
    
    def write(self, data: Any):
        raise NotImplementedError


class ListSink(Sink):
    """List sink"""
    
    def __init__(self):
        self.items = []
    
    def write(self, data: Any):
        self.items.append(data)
    
    def get_items(self) -> List:
        return self.items


class DictSink(Sink):
    """Dictionary sink"""
    
    def __init__(self, key_field: str):
        self.key_field = key_field
        self.items = {}
    
    def write(self, data: Any):
        if isinstance(data, dict) and self.key_field in data:
            self.items[data[self.key_field]] = data


class NullSink(Sink):
    """Null sink - discards all"""
    
    def write(self, data: Any):
        pass
