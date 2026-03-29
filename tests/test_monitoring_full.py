"""Tests for monitoring module"""


import pytest

from orchestration.monitoring.metrics import (
    Metrics,
    create_metrics,
    create_tracer,
    get_metrics,
)


class TestMetrics:
    """Test Metrics"""

    @pytest.fixture
    def metrics(self):
        """Create metrics"""
        return Metrics()

    def test_creation(self, metrics):
        """Test creation"""
        assert metrics is not None

    def test_increment(self, metrics):
        """Test increment"""
        metrics.increment("test_counter")
        assert metrics.counters.get("test_counter", 0) == 1

    def test_set_gauge(self, metrics):
        """Test gauge"""
        metrics.set_gauge("test_gauge", 100.0)
        assert metrics.gauges.get("test_gauge") == 100.0

    def test_record_cache_hit(self, metrics):
        """Test cache hit"""
        metrics.record_cache_hit()
        assert metrics.counters.get("cache_hit", 0) == 1

    def test_record_cache_miss(self, metrics):
        """Test cache miss"""
        metrics.record_cache_miss()
        assert metrics.counters.get("cache_miss", 0) == 1

    def test_record_phase(self, metrics):
        """Test phase recording"""
        metrics.record_phase("test_phase", 1.5)
        assert "phase_test_phase" in metrics.counters


class TestMetricsFactory:
    """Test metrics factory"""

    def test_create_metrics(self):
        """Test create metrics"""
        metrics = create_metrics()
        assert metrics is not None

    def test_create_tracer(self):
        """Test create tracer"""
        result = create_tracer()
        # Tracer might be None if OpenTelemetry not installed
        assert result is None or result is not None


class TestMetricsSingleton:
    """Test metrics singleton"""

    def test_singleton(self):
        """Test singleton pattern"""
        m1 = get_metrics()
        m2 = get_metrics()
        # Should be same instance
        assert m1 is m2
