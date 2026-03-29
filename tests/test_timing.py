"""Tests for Timing"""

import asyncio
import time

import pytest

from orchestration.timing import (
    RateTracker,
    Stopwatch,
    Timer,
    async_timed,
    get_timer,
    timed,
)


class TestTimer:
    """Test Timer"""

    def test_creation(self):
        """Test creation"""
        timer = Timer("test")
        assert timer.name == "test"
        assert timer.elapsed() == 0.0

    def test_start_stop(self):
        """Test start stop"""
        timer = Timer("test")
        timer.start()
        time.sleep(0.05)
        elapsed = timer.stop()
        assert elapsed >= 0.05

    def test_context_manager(self):
        """Test context manager"""
        with Timer("test") as timer:
            time.sleep(0.05)
        assert timer.elapsed() >= 0.05

    def test_elapsed_before_start(self):
        """Test elapsed before start"""
        timer = Timer("test")
        assert timer.elapsed() == 0.0


class TestTimedDecorator:
    """Test timed decorator"""

    def test_timed(self):
        """Test timed decorator"""
        @timed
        def slow_function():
            time.sleep(0.05)
            return "result"

        result = slow_function()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_async_timed(self):
        """Test async timed decorator"""

        @async_timed
        async def slow_async():
            await asyncio.sleep(0.05)
            return "result"

        result = await slow_async()
        assert result == "result"


class TestStopwatch:
    """Test Stopwatch"""

    def test_creation(self):
        """Test creation"""
        sw = Stopwatch()
        assert sw._start_time is None

    def test_lap(self):
        """Test lap"""
        sw = Stopwatch()
        sw.start()
        time.sleep(0.05)
        lap1 = sw.lap()
        time.sleep(0.05)
        lap2 = sw.lap()

        assert lap1 >= 0.05
        assert lap2 >= lap1

    def test_stop(self):
        """Test stop"""
        sw = Stopwatch()
        sw.start()
        time.sleep(0.05)
        total = sw.stop()
        assert total >= 0.05

    def test_get_laps(self):
        """Test get laps"""
        sw = Stopwatch()
        sw.start()
        sw.lap()
        sw.lap()
        laps = sw.get_laps()
        assert len(laps) == 2


class TestRateTracker:
    """Test RateTracker"""

    def test_creation(self):
        """Test creation"""
        tracker = RateTracker(window=60.0)
        assert tracker.window == 60.0

    def test_record(self):
        """Test record"""
        tracker = RateTracker()
        tracker.record()
        tracker.record()
        assert tracker.count() == 2

    def test_rate(self):
        """Test rate"""
        tracker = RateTracker()
        tracker.record()
        time.sleep(0.1)
        tracker.record()
        rate = tracker.rate()
        assert rate > 0


class TestGetTimer:
    """Test get_timer"""

    def test_get_timer(self):
        """Test get timer"""
        timer = get_timer("test")
        assert timer.name == "test"
