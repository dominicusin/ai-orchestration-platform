"""Tests for monitoring"""

from orchestration.monitoring.exporters import JSONExporter, PrometheusExporter
from orchestration.monitoring.metrics import Metrics, get_metrics


class TestMetrics:
    """Test Metrics"""

    def test_metrics_creation(self):
        """Test metrics creation"""
        m = Metrics()
        assert m is not None

    def test_increment(self):
        """Test increment"""
        m = Metrics()
        m.increment("test")
        assert m.get("test") == 1
        m.increment("test", 5)
        assert m.get("test") == 6

    def test_set_gauge(self):
        """Test gauge"""
        m = Metrics()
        m.set_gauge("cpu", 0.75)
        assert m.gauges.get("cpu") == 0.75

    def test_record_cache_hit(self):
        """Test cache hit"""
        m = Metrics()
        m.record_cache_hit()
        assert m.get("cache_hit") == 1

    def test_record_cache_miss(self):
        """Test cache miss"""
        m = Metrics()
        m.record_cache_miss()
        assert m.get("cache_miss") == 1

    def test_record_phase(self):
        """Test phase recording"""
        m = Metrics()
        m.record_phase("test_phase", 1.5)
        assert "test_phase" in m.timers

    def test_export_json(self):
        """Test JSON export"""
        m = Metrics()
        m.increment("test")
        data = m.export_json()
        assert "counters" in data
        assert data["counters"]["test"] == 1


class TestGetMetrics:
    """Test get_metrics singleton"""

    def test_singleton(self):
        """Test singleton"""
        m1 = get_metrics()
        m2 = get_metrics()
        assert m1 is m2


class TestJSONExporter:
    """Test JSON exporter"""

    def test_export(self):
        """Test export"""
        exporter = JSONExporter()
        data = {"test": 1}
        result = exporter.export(data)
        assert result is True


class TestPrometheusExporter:
    """Test Prometheus exporter"""

    def test_export(self):
        """Test export"""
        exporter = PrometheusExporter()
        data = {"runtime_seconds": 10, "phases": {}, "ai": {}}
        result = exporter.export(data)
        assert result is True
