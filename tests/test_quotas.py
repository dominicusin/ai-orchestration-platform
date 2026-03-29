"""Tests for Quotas"""

import time

import pytest

from orchestration.quotas import (
    Quota,
    QuotaManager,
    get_quota_manager,
)


class TestQuota:
    """Test Quota"""

    def test_creation(self):
        """Test creation"""
        quota = Quota(name="test", limit=100)
        assert quota.name == "test"
        assert quota.limit == 100
        assert quota.used == 0


class TestQuotaManager:
    """Test QuotaManager"""

    @pytest.fixture
    def manager(self):
        """Create manager"""
        return QuotaManager()

    def test_creation(self, manager):
        """Test creation"""
        assert manager is not None

    def test_create_quota(self, manager):
        """Test create quota"""
        manager.create_quota("api", 1000)
        assert "api" in manager._quotas

    def test_check_available(self, manager):
        """Test check available"""
        manager.create_quota("api", 100)
        assert manager.check("api", 50) is True

    def test_check_exceeded(self, manager):
        """Test check exceeded"""
        manager.create_quota("api", 100)
        assert manager.check("api", 150) is False

    def test_consume(self, manager):
        """Test consume"""
        manager.create_quota("api", 100)
        assert manager.consume("api", 50) is True
        assert manager._quotas["api"].used == 50

    def test_consume_fail(self, manager):
        """Test consume fail"""
        manager.create_quota("api", 100)
        manager.consume("api", 100)
        assert manager.consume("api", 1) is False

    def test_get_usage(self, manager):
        """Test get usage"""
        manager.create_quota("api", 100)
        manager.consume("api", 30)

        usage = manager.get_usage("api")
        assert usage["used"] == 30
        assert usage["remaining"] == 70

    def test_set_unlimited(self, manager):
        """Test unlimited"""
        manager.create_quota("api", 100)
        manager.set_unlimited("api", True)

        assert manager.consume("api", 10000) is True

    def test_reset(self, manager):
        """Test quota reset"""
        manager.create_quota("api", 100, reset_interval_seconds=1)
        manager.consume("api", 50)

        # Wait for reset
        time.sleep(1.1)
        assert manager.check("api", 60) is True


class TestQuotaManagerSingleton:
    """Test singleton"""

    def test_singleton(self):
        """Test singleton"""
        m1 = get_quota_manager()
        m2 = get_quota_manager()
        assert m1 is m2
