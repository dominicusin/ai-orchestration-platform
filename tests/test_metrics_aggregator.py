"""Tests for Metrics Aggregator"""

import time

import pytest

from orchestration.metrics_aggregator import (
    MetricPoint,
    MetricsAggregator,
    get_metrics_aggregator,
)


class TestMetricPoint:
    """Test MetricPoint"""

    def test_creation(self):
        """Test creation"""
        point = MetricPoint(
            timestamp=time.time(),
            value=10.5,
            tags={"env": "test"},
        )
        assert point.value == 10.5
        assert point.tags["env"] == "test"


class TestMetricsAggregator:
    """Test MetricsAggregator"""

    @pytest.fixture
    def agg(self):
        """Create aggregator"""
        return MetricsAggregator()

    def test_creation(self, agg):
        """Test creation"""
        assert agg is not None

    def test_record(self, agg):
        """Test record"""
        agg.record("test.metric", 10.0)
        points = agg._metrics["test.metric"]
        assert len(points) == 1
        assert points[0].value == 10.0

    def test_record_with_tags(self, agg):
        """Test record with tags"""
        agg.record("test.metric", 10.0, {"env": "prod"})
        points = agg._metrics["test.metric"]
        assert points[0].tags["env"] == "prod"

    def test_increment(self, agg):
        """Test increment"""
        agg.increment("requests")
        agg.increment("requests")
        agg.increment("requests", 5)
        assert agg.get_counter("requests") == 7

    def test_gauge(self, agg):
        """Test gauge"""
        agg.gauge("memory", 512.5)
        assert agg.get_gauge("memory") == 512.5

    def test_query(self, agg):
        """Test query"""
        agg.record("test.metric", 10.0)
        time.sleep(0.01)
        agg.record("test.metric", 20.0)

        points = agg.query("test.metric")
        assert len(points) == 2

    def test_query_with_time_filter(self, agg):
        """Test query with time filter"""
        agg.record("test.metric", 10.0)
        time.sleep(0.01)
        start = time.time()
        agg.record("test.metric", 20.0)

        points = agg.query("test.metric", start_time=start)
        assert len(points) == 1

    def test_aggregate_avg(self, agg):
        """Test aggregate avg"""
        agg.record("test.metric", 10.0)
        agg.record("test.metric", 20.0)
        agg.record("test.metric", 30.0)

        result = agg.aggregate("test.metric", "avg")
        assert result == 20.0

    def test_aggregate_sum(self, agg):
        """Test aggregate sum"""
        agg.record("test.metric", 10.0)
        agg.record("test.metric", 20.0)

        result = agg.aggregate("test.metric", "sum")
        assert result == 30.0

    def test_aggregate_min(self, agg):
        """Test aggregate min"""
        agg.record("test.metric", 30.0)
        agg.record("test.metric", 10.0)
        agg.record("test.metric", 20.0)

        result = agg.aggregate("test.metric", "min")
        assert result == 10.0

    def test_aggregate_max(self, agg):
        """Test aggregate max"""
        agg.record("test.metric", 10.0)
        agg.record("test.metric", 30.0)
        agg.record("test.metric", 20.0)

        result = agg.aggregate("test.metric", "max")
        assert result == 30.0

    def test_aggregate_count(self, agg):
        """Test aggregate count"""
        agg.record("test.metric", 10.0)
        agg.record("test.metric", 20.0)

        result = agg.aggregate("test.metric", "count")
        assert result == 2

    def test_get_summary(self, agg):
        """Test get summary"""
        agg.record("test.metric", 10.0)
        agg.increment("requests")
        agg.gauge("memory", 512.0)

        summary = agg.get_summary()
        assert "test.metric" in summary["metrics"]
        assert "requests" in summary["counters"]
        assert "memory" in summary["gauges"]

    def test_clear(self, agg):
        """Test clear"""
        agg.record("test.metric", 10.0)
        agg.increment("requests")
        agg.gauge("memory", 512.0)

        agg.clear()

        assert len(agg._metrics) == 0
        assert len(agg._counters) == 0
        assert len(agg._gauges) == 0


class TestMetricsAggregatorSingleton:
    """Test singleton"""

    def test_singleton(self):
        """Test singleton"""
        agg1 = get_metrics_aggregator()
        agg2 = get_metrics_aggregator()
        assert agg1 is agg2
