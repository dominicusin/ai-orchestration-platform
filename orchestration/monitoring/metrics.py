"""Monitoring utilities"""

import time
import logging
from typing import Dict, Any

logger = logging.getLogger("orchestration.monitoring.metrics")


class Metrics:
    """Simple metrics"""
    
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
    
    def increment(self, name: str, value: int = 1):
        self.counters[name] = self.counters.get(name, 0) + value
    
    def set_gauge(self, name: str, value: float):
        self.gauges[name] = value
    
    def get(self, name: str) -> int:
        return self.counters.get(name, 0)


_metrics = None


def get_metrics() -> Metrics:
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics