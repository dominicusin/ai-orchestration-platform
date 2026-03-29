"""Pipeline analytics aggregators"""

import logging
from collections import defaultdict

logger = logging.getLogger("orchestration.aggregators")


class Aggregator:
    """Base aggregator"""

    def aggregate(self, data: list[dict]) -> dict:
        raise NotImplementedError


class SumAggregator(Aggregator):
    """Sum values"""

    def __init__(self, field: str):
        self.field = field

    def aggregate(self, data: list[dict]) -> dict:
        return {"sum": sum(item.get(self.field, 0) for item in data)}


class AvgAggregator(Aggregator):
    """Average values"""

    def __init__(self, field: str):
        self.field = field

    def aggregate(self, data: list[dict]) -> dict:
        values = [item.get(self.field, 0) for item in data]
        return {"avg": sum(values) / len(values) if values else 0}


class CountAggregator(Aggregator):
    """Count items"""

    def __init__(self, field: str = None):
        self.field = field

    def aggregate(self, data: list[dict]) -> dict:
        if self.field:
            return {"count": sum(1 for item in data if self.field in item)}
        return {"count": len(data)}


class GroupByAggregator(Aggregator):
    """Group by field"""

    def __init__(self, field: str, aggregator: Aggregator):
        self.field = field
        self.aggregator = aggregator

    def aggregate(self, data: list[dict]) -> dict:
        groups = defaultdict(list)

        for item in data:
            key = item.get(self.field, "unknown")
            groups[key].append(item)

        return {
            key: self.aggregator.aggregate(items)
            for key, items in groups.items()
        }
