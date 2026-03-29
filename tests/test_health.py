"""Tests for Health Check"""

import asyncio

import pytest

from orchestration.health import (
    HealthCheck,
    HealthCheckManager,
    HealthCheckResult,
    HealthReport,
    HealthStatus,
)


class TestHealthStatus:
    """Test HealthStatus"""

    def test_values(self):
        """Test enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestHealthCheckResult:
    """Test HealthCheckResult"""

    def test_creation(self):
        """Test creation"""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
            latency_ms=10.5,
        )
        assert result.name == "test"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms == 10.5


class TestHealthCheck:
    """Test HealthCheck"""

    @pytest.fixture
    def check(self):
        """Create check"""
        async def test_func():
            return True

        return HealthCheck("test_check", test_func, timeout=5.0)

    def test_creation(self, check):
        """Test creation"""
        assert check.name == "test_check"
        assert check.timeout == 5.0

    @pytest.mark.asyncio
    async def test_execute_success(self, check):
        """Test successful execution"""
        result = await check.execute()
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_execute_failure(self):
        """Test failed execution"""
        def fail_func():
            raise Exception("Test error")

        check = HealthCheck("fail", fail_func)
        result = await check.execute()
        assert result.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test timeout"""
        async def slow_func():
            await asyncio.sleep(10)

        check = HealthCheck("slow", slow_func, timeout=0.1)
        result = await check.execute()
        assert result.status == HealthStatus.UNHEALTHY
        assert "Timeout" in result.message


class TestHealthCheckManager:
    """Test HealthCheckManager"""

    @pytest.fixture
    def manager(self):
        """Create manager"""
        return HealthCheckManager()

    def test_creation(self, manager):
        """Test creation"""
        assert len(manager._checks) == 0

    def test_register(self, manager):
        """Test register"""
        def test_func():
            return True

        manager.register("test", test_func)
        assert len(manager._checks) == 1
        assert manager._checks[0].name == "test"

    @pytest.mark.asyncio
    async def test_check_all(self, manager):
        """Test check all"""
        async def healthy_check():
            return True

        manager.register("check1", healthy_check)
        manager.register("check2", healthy_check)

        report = await manager.check_all()
        assert isinstance(report, HealthReport)
        assert len(report.checks) == 2

    @pytest.mark.asyncio
    async def test_check_all_with_failure(self, manager):
        """Test check all with failure"""
        async def healthy():
            return True

        async def unhealthy():
            return False

        manager.register("healthy", healthy)
        manager.register("unhealthy", unhealthy)

        report = await manager.check_all()
        assert report.overall_status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_get_last_report(self, manager):
        """Test get last report"""
        async def test_check():
            return True

        manager.register("test", test_check)
        await manager.check_all()

        report = manager.get_last_report()
        assert report is not None

    def test_get_status_summary(self, manager):
        """Test status summary"""
        summary = manager.get_status_summary()
        assert "status" in summary


class TestHealthReport:
    """Test HealthReport"""

    def test_creation(self):
        """Test creation"""
        results = [
            HealthCheckResult(name="c1", status=HealthStatus.HEALTHY),
            HealthCheckResult(name="c2", status=HealthStatus.HEALTHY),
        ]
        report = HealthReport(
            overall_status=HealthStatus.HEALTHY,
            checks=results,
            duration_ms=10.0,
        )
        assert report.overall_status == HealthStatus.HEALTHY
        assert len(report.checks) == 2
