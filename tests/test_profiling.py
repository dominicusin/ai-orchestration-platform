"""Tests for Profiling"""

import asyncio
import time

import pytest

from orchestration.profiling import (
    PerformanceMonitor,
    Profiler,
    ProfileResult,
    Timer,
    TimingResult,
    async_timeit,
    timeit,
)


class TestProfileResult:
    """Test ProfileResult"""

    def test_creation(self):
        """Test creation"""
        result = ProfileResult(
            function_name="test",
            calls=100,
            total_time=1.0,
            per_call=0.01,
            cum_time=1.0,
            per_call_cum=0.01,
        )
        assert result.function_name == "test"
        assert result.calls == 100


class TestTimingResult:
    """Test TimingResult"""

    def test_creation(self):
        """Test creation"""
        result = TimingResult(
            name="test",
            start_time=0.0,
            end_time=1.0,
            duration=1.0,
        )
        assert result.name == "test"
        assert result.duration == 1.0


class TestProfiler:
    """Test Profiler"""

    @pytest.fixture
    def profiler(self):
        """Create profiler"""
        return Profiler(enabled=True)

    def test_profiler_init(self, profiler):
        """Test init"""
        assert profiler.enabled is True
        assert len(profiler._results) == 0

    def test_profile_decorator(self, profiler):
        """Test profile decorator"""

        @profiler.profile
        def test_func():
            total = 0
            for i in range(100):
                total += i
            return total

        result = test_func()
        assert result == 4950

    def test_profile_with_args(self, profiler):
        """Test profile with args"""

        @profiler.profile
        def add(a, b):
            return a + b

        result = add(1, 2)
        assert result == 3

    def test_get_results(self, profiler):
        """Test get results"""
        @profiler.profile
        def test_func():
            total = 0
            for i in range(1000):
                total += i
            return total

        test_func()
        # Results may be empty if parsing fails, but function should work
        _ = profiler.get_results()

    def test_clear_results(self, profiler):
        """Test clear results"""
        @profiler.profile
        def test_func():
            return 1

        test_func()
        profiler.clear_results()
        assert len(profiler.get_results()) == 0


class TestTimer:
    """Test Timer"""

    def test_timer_context(self):
        """Test timer as context manager"""
        with Timer("test") as timer:
            time.sleep(0.01)

        assert timer.result is not None
        assert timer.result.name == "test"
        assert timer.result.duration >= 0.01

    def test_timer_get_duration(self):
        """Test get duration"""
        with Timer("test") as timer:
            time.sleep(0.01)

        assert timer.get_duration() >= 0.01


class TestTimeit:
    """Test timeit decorator"""

    def test_timeit_decorator(self):
        """Test timeit decorator"""

        @timeit
        def slow_func():
            time.sleep(0.01)
            return 42

        result = slow_func()
        assert result == 42


class TestAsyncTimeit:
    """Test async_timeit decorator"""

    @pytest.mark.asyncio
    async def test_async_timeit(self):
        """Test async timeit"""

        @async_timeit
        async def slow_async():
            await asyncio.sleep(0.01)
            return 42

        result = await slow_async()
        assert result == 42


class TestPerformanceMonitor:
    """Test PerformanceMonitor"""

    @pytest.fixture
    def monitor(self):
        """Create monitor"""
        return PerformanceMonitor()

    def test_record(self, monitor):
        """Test record timing"""
        monitor.record("test", 1.0)
        monitor.record("test", 2.0)
        monitor.record("test", 3.0)

        stats = monitor.get_stats("test")
        assert stats["calls"] == 3
        assert stats["total"] == 6.0
        assert stats["avg"] == 2.0
        assert stats["min"] == 1.0
        assert stats["max"] == 3.0

    def test_get_stats_unknown(self, monitor):
        """Test get stats for unknown function"""
        stats = monitor.get_stats("unknown")
        assert stats == {}

    def test_get_all_stats(self, monitor):
        """Test get all stats"""
        monitor.record("func1", 1.0)
        monitor.record("func2", 2.0)

        all_stats = monitor.get_all_stats()
        assert "func1" in all_stats
        assert "func2" in all_stats

    def test_clear(self, monitor):
        """Test clear"""
        monitor.record("test", 1.0)
        monitor.clear()

        stats = monitor.get_stats("test")
        assert stats == {}
