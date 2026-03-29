"""
Metrics aggregator
Агрегатор метрик для аналитики
"""

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class MetricPoint:
    """Точка метрики"""
    timestamp: float
    value: float
    tags: dict = field(default_factory=dict)


class MetricsAggregator:
    """
    Агрегатор метрик с поддержкой:
    - Временных рядов
    - Агрегации (avg, sum, min, max, count)
    - Тегирования
    - Экспорта
    """

    def __init__(self):
        self._metrics: dict[str, list[MetricPoint]] = defaultdict(list)
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}

    def record(self, name: str, value: float, tags: dict = None):
        """Запись метрики"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            tags=tags or {},
        )
        self._metrics[name].append(point)

    def increment(self, name: str, value: int = 1):
        """Инкремент счётчика"""
        self._counters[name] += value

    def gauge(self, name: str, value: float):
        """Установка gauge"""
        self._gauges[name] = value

    def query(
        self,
        name: str,
        start_time: float = None,
        end_time: float = None,
        tags: dict = None,
    ) -> list[MetricPoint]:
        """Запрос метрик"""
        points = self._metrics.get(name, [])

        if start_time:
            points = [p for p in points if p.timestamp >= start_time]
        if end_time:
            points = [p for p in points if p.timestamp <= end_time]
        if tags:
            points = [p for p in points if all(p.tags.get(k) == v for k, v in tags.items())]

        return points

    def aggregate(
        self,
        name: str,
        func: str = "avg",
        start_time: float = None,
        end_time: float = None,
    ) -> float:
        """Агрегация метрик"""
        points = self.query(name, start_time, end_time)
        if not points:
            return 0.0

        values = [p.value for p in points]

        if func == "avg":
            return sum(values) / len(values)
        elif func == "sum":
            return sum(values)
        elif func == "min":
            return min(values)
        elif func == "max":
            return max(values)
        elif func == "count":
            return len(values)
        return 0.0

    def get_counter(self, name: str) -> int:
        """Получение счётчика"""
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        """Получение gauge"""
        return self._gauges.get(name, 0.0)

    def get_summary(self) -> dict:
        """Получение сводки"""
        return {
            "metrics": list(self._metrics.keys()),
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
        }

    def export_json(self, path: str):
        """Экспорт в JSON"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                name: [
                    {"timestamp": p.timestamp, "value": p.value, "tags": p.tags}
                    for p in points
                ]
                for name, points in self._metrics.items()
            },
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
        }
        Path(path).write_text(json.dumps(data, indent=2))

    def clear(self):
        """Очистка"""
        self._metrics.clear()
        self._counters.clear()
        self._gauges.clear()


# Singleton
_metrics_aggregator: MetricsAggregator | None = None


def get_metrics_aggregator() -> MetricsAggregator:
    """Получение агрегатора"""
    global _metrics_aggregator
    if _metrics_aggregator is None:
        _metrics_aggregator = MetricsAggregator()
    return _metrics_aggregator
