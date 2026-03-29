"""Tests for Resource Managers"""

import pytest

from orchestration.resource_managers import (
    CPUMonitor,
    DiskManager,
    MemoryManager,
    ResourceLimit,
    ResourceMonitor,
    ResourceUsage,
    get_resource_monitor,
)


class TestResourceLimit:
    """Test ResourceLimit"""

    def test_creation(self):
        """Test creation"""
        limits = ResourceLimit(
            max_memory_percent=80.0,
            max_disk_percent=85.0,
            max_cpu_percent=90.0,
        )
        assert limits.max_memory_percent == 80.0
        assert limits.max_disk_percent == 85.0


class TestResourceUsage:
    """Test ResourceUsage"""

    def test_creation(self):
        """Test creation"""
        usage = ResourceUsage(
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=8192.0,
            memory_available_mb=4096.0,
            disk_used_gb=100.0,
            disk_free_gb=400.0,
            disk_percent=20.0,
        )
        assert usage.cpu_percent == 50.0
        assert usage.memory_percent == 60.0


class TestResourceMonitor:
    """Test ResourceMonitor"""

    @pytest.fixture
    def monitor(self):
        """Create monitor"""
        return ResourceMonitor()

    def test_creation(self, monitor):
        """Test creation"""
        assert monitor is not None

    def test_get_usage(self, monitor):
        """Test get usage"""
        usage = monitor.get_usage()
        assert isinstance(usage, ResourceUsage)
        assert usage.cpu_percent >= 0
        assert usage.memory_percent >= 0
        assert usage.disk_percent >= 0

    def test_check_limits(self, monitor):
        """Test check limits"""
        result = monitor.check_limits()
        assert "usage" in result
        assert "warnings" in result
        assert "within_limits" in result

    def test_set_limits(self, monitor):
        """Test set limits"""
        limits = ResourceLimit(max_memory_percent=50.0)
        monitor.set_limits(limits)
        assert monitor._limits.max_memory_percent == 50.0

    def test_get_process_info(self, monitor):
        """Test get process info"""
        info = monitor.get_process_info()
        assert "pid" in info
        assert "cpu_percent" in info
        assert "memory_mb" in info


class TestMemoryManager:
    """Test MemoryManager"""

    @pytest.fixture
    def manager(self):
        """Create manager"""
        return MemoryManager()

    def test_creation(self, manager):
        """Test creation"""
        assert manager.threshold_percent == 85.0

    def test_get_memory_info(self, manager):
        """Test get memory info"""
        info = manager.get_memory_info()
        assert "total_mb" in info
        assert "available_mb" in info
        assert "percent" in info

    def test_is_memory_available(self, manager):
        """Test is memory available"""
        result = manager.is_memory_available(1.0)
        assert isinstance(result, bool)

    def test_is_critical(self, manager):
        """Test is critical"""
        result = manager.is_critical()
        assert isinstance(result, bool)


class TestDiskManager:
    """Test DiskManager"""

    @pytest.fixture
    def manager(self):
        """Create manager"""
        return DiskManager()

    def test_creation(self, manager):
        """Test creation"""
        assert manager.path == "/"

    def test_get_disk_info(self, manager):
        """Test get disk info"""
        info = manager.get_disk_info()
        assert "total_gb" in info
        assert "free_gb" in info
        assert "percent" in info

    def test_is_critical(self, manager):
        """Test is critical"""
        result = manager.is_critical()
        assert isinstance(result, bool)


class TestCPUMonitor:
    """Test CPUMonitor"""

    @pytest.fixture
    def monitor(self):
        """Create monitor"""
        return CPUMonitor()

    def test_creation(self, monitor):
        """Test creation"""
        assert monitor.threshold_percent == 95.0

    def test_get_cpu_info(self, monitor):
        """Test get CPU info"""
        info = monitor.get_cpu_info()
        assert "physical_cores" in info
        assert "logical_cores" in info
        assert "percent" in info

    def test_is_critical(self, monitor):
        """Test is critical"""
        result = monitor.is_critical()
        assert isinstance(result, bool)


class TestResourceMonitorSingleton:
    """Test singleton"""

    def test_singleton(self):
        """Test singleton"""
        m1 = get_resource_monitor()
        m2 = get_resource_monitor()
        assert m1 is m2
