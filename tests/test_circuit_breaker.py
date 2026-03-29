"""Tests for Circuit Breaker"""

import time

import pytest

from orchestration.circuit_states import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerStats,
    CircuitState,
    get_breaker_manager,
)


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig"""

    def test_creation(self):
        """Test creation"""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=3,
            timeout=60.0,
        )
        assert config.failure_threshold == 10
        assert config.success_threshold == 3
        assert config.timeout == 60.0

    def test_defaults(self):
        """Test default values"""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 30.0


class TestCircuitBreakerStats:
    """Test CircuitBreakerStats"""

    def test_creation(self):
        """Test creation"""
        stats = CircuitBreakerStats()
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.state == CircuitState.CLOSED


class TestCircuitBreaker:
    """Test CircuitBreaker"""

    @pytest.fixture
    def breaker(self):
        """Create breaker"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=1.0,
        )
        return CircuitBreaker("test", config)

    def test_creation(self, breaker):
        """Test creation"""
        assert breaker.name == "test"
        assert breaker.state == CircuitState.CLOSED

    def test_initial_closed_state(self, breaker):
        """Test initial closed state"""
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_successful_call(self, breaker):
        """Test successful call"""
        async def success_func():
            return "success"

        result = await breaker.execute(success_func)
        assert result == "success"
        assert breaker._stats.successful_calls == 1

    @pytest.mark.asyncio
    async def test_failed_call(self, breaker):
        """Test failed call"""
        async def fail_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await breaker.execute(fail_func)

        assert breaker._stats.failed_calls == 1

    @pytest.mark.asyncio
    async def test_opens_after_failures(self, breaker):
        """Test opens after threshold"""
        async def fail_func():
            raise ValueError("error")

        for _ in range(3):
            try:
                await breaker.execute(fail_func)
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_rejects_when_open(self, breaker):
        """Test rejects when open"""
        # Force open state
        breaker._state = CircuitState.OPEN

        async def test_func():
            return "test"

        with pytest.raises(CircuitBreakerOpenError):
            await breaker.execute(test_func)

        assert breaker._stats.rejected_calls == 1

    @pytest.mark.asyncio
    async def test_half_open_transition(self, breaker):
        """Test half-open transition"""
        # Open the circuit
        breaker._state = CircuitState.OPEN
        breaker._last_failure_time = time.time() - 2.0  # Past timeout

        # Should transition to half-open
        assert breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success(self, breaker):
        """Test half-open to closed"""
        breaker._state = CircuitState.HALF_OPEN

        async def success():
            return "ok"

        # Multiple successes should close
        for _ in range(2):
            await breaker.execute(success)

        assert breaker.state == CircuitState.CLOSED

    def test_reset(self, breaker):
        """Test reset"""
        breaker._state = CircuitState.OPEN
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager"""

    def test_get_breaker(self):
        """Test get breaker"""
        manager = get_breaker_manager()
        breaker = manager.get_breaker("test1")
        assert breaker is not None
        assert breaker.name == "test1"

    def test_get_existing_breaker(self):
        """Test get existing"""
        manager = get_breaker_manager()
        breaker1 = manager.get_breaker("test2")
        breaker2 = manager.get_breaker("test2")
        assert breaker1 is breaker2

    def test_get_all_stats(self):
        """Test get all stats"""
        manager = get_breaker_manager()
        manager.get_breaker("test3")

        stats = manager.get_all_stats()
        assert "test3" in stats
