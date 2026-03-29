"""Pipeline monitoring and observability"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("orchestration.observability")


@dataclass
class Span:
    """Tracing span"""
    name: str
    start_time: float
    end_time: float | None = None
    tags: dict[str, Any] = field(default_factory=dict)
    logs: list[dict] = field(default_factory=list)

    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time


class Tracer:
    """Distributed tracing"""

    def __init__(self, service_name: str = "pipeline"):
        self.service_name = service_name
        self.spans: list[Span] = []
        self._current_span: Span | None = None

    def start_span(self, name: str, tags: dict = None) -> Span:
        """Start a new span"""
        span = Span(
            name=name,
            start_time=time.time(),
            tags=tags or {},
        )

        self._current_span = span
        self.spans.append(span)

        return span

    def end_span(self, span: Span):
        """End a span"""
        span.end_time = time.time()
        self._current_span = None

    def log(self, key: str, value: Any):
        """Log to current span"""
        if self._current_span:
            self._current_span.logs.append({
                "time": time.time(),
                "key": key,
                "value": str(value),
            })

    def get_traces(self, limit: int = 100) -> list[dict]:
        """Get traces"""
        return [
            {
                "name": s.name,
                "duration": s.duration,
                "tags": s.tags,
                "logs": s.logs,
            }
            for s in self.spans[-limit:]
        ]


class MetricsCollector:
    """Collect custom metrics"""

    def __init__(self):
        self.counters: dict[str, int] = defaultdict(int)
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = defaultdict(list)

    def increment(self, name: str, value: int = 1):
        """Increment counter"""
        self.counters[name] += value

    def decrement(self, name: str, value: int = 1):
        """Decrement counter"""
        self.counters[name] -= value

    def gauge(self, name: str, value: float):
        """Set gauge"""
        self.gauges[name] = value

    def histogram(self, name: str, value: float):
        """Record histogram value"""
        self.histograms[name].append(value)

    def get_metrics(self) -> dict:
        """Get all metrics"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                k: {
                    "count": len(v),
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                    "avg": sum(v) / len(v) if v else 0,
                }
                for k, v in self.histograms.items()
            },
        }


class PipelineObserver:
    """Observe pipeline execution"""

    def __init__(self):
        self.tracer = Tracer()
        self.metrics = MetricsCollector()
        self.events: list[dict] = []

    def record_event(self, event_type: str, data: dict):
        """Record pipeline event"""
        self.events.append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })

    def get_summary(self) -> dict:
        """Get observability summary"""
        return {
            "traces": self.tracer.get_traces(10),
            "metrics": self.metrics.get_metrics(),
            "events": self.events[-20:],
        }


# Global observer
_observer: PipelineObserver | None = None


def get_observer() -> PipelineObserver:
    """Get pipeline observer"""
    global _observer
    if _observer is None:
        _observer = PipelineObserver()
    return _observer
