"""Monitoring utilities"""

import logging

logger = logging.getLogger("orchestration.monitoring.metrics")


class Metrics:
    """Simple metrics"""

    def __init__(self):
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}
        self.timers: dict[str, float] = {}

    def increment(self, name: str, value: int = 1):
        self.counters[name] = self.counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float):
        self.gauges[name] = value

    def get(self, name: str) -> int:
        return self.counters.get(name, 0)

    def record_cache_hit(self):
        self.increment("cache_hit")

    def record_cache_miss(self):
        self.increment("cache_miss")

    def record_phase(self, phase: str, duration: float):
        self.timers[phase] = duration
        self.increment(f"phase_{phase}")

    def export_json(self, path: str = None) -> dict:
        result = {
            "counters": self.counters,
            "gauges": self.gauges,
            "timers": self.timers,
        }
        if path:
            import json
            from pathlib import Path
            Path(path).write_text(json.dumps(result, indent=2))
        return result

    def close(self):
        pass


_metrics = None


def get_metrics() -> Metrics:
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics


def create_metrics() -> Metrics:
    return Metrics()


def create_tracer():
    """Create tracer for monitoring"""
    return {"name": "tracer"}
