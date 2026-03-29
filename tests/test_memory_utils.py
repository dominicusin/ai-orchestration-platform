"""Tests for Memory Utilities"""

import gc
from dataclasses import dataclass

import pytest

from orchestration.memory_utils import (
    MemoryOptimizer,
    MemorySnapshot,
    MemoryStats,
    MemoryTracker,
)


class TestMemorySnapshot:
    """Test MemorySnapshot"""

    def test_creation(self):
        """Test snapshot creation"""
        snapshot = MemorySnapshot(
            timestamp="2024-01-01T00:00:00",
            rss_mb=100.0,
            vms_mb=200.0,
            objects=1000,
        )
        assert snapshot.rss_mb == 100.0
        assert snapshot.objects == 1000


class TestMemoryStats:
    """Test MemoryStats"""

    def test_delta_mb(self):
        """Test delta calculation"""
        stats = MemoryStats(initial_mb=100.0, current_mb=150.0)
        assert stats.delta_mb == 50.0

    def test_delta_percent(self):
        """Test delta percent"""
        stats = MemoryStats(initial_mb=100.0, current_mb=150.0)
        assert stats.delta_percent == 50.0

    def test_zero_initial(self):
        """Test zero initial"""
        stats = MemoryStats(initial_mb=0.0, current_mb=100.0)
        assert stats.delta_percent == 0.0


class TestMemoryTracker:
    """Test MemoryTracker"""

    @pytest.fixture
    def tracker(self):
        """Create tracker"""
        return MemoryTracker()

    def test_tracker_init(self, tracker):
        """Test tracker init"""
        assert tracker._enabled is False
        assert len(tracker._snapshots) == 0

    def test_start_stop(self, tracker):
        """Test start and stop"""
        tracker.start()
        assert tracker._enabled is True

        tracker.stop()
        assert tracker._enabled is False
        assert tracker.stats.initial_mb > 0

    def test_take_snapshot(self, tracker):
        """Test take snapshot"""
        tracker.start()
        snapshot = tracker.take_snapshot()

        assert snapshot is not None
        assert snapshot.rss_mb > 0
        assert snapshot.objects > 0

        tracker.stop()

    def test_take_multiple_snapshots(self, tracker):
        """Test multiple snapshots"""
        tracker.start()
        for _ in range(5):
            tracker.take_snapshot()

        assert len(tracker.get_snapshots()) == 5
        tracker.stop()

    def test_track_object(self, tracker):
        """Test track object"""
        tracker.start()

        class Trackable:
            pass

        obj = Trackable()
        tracker.track_object(obj)

        assert len(tracker._tracked_objects) == 1

        del obj
        gc.collect()

        tracker.stop()

    def test_force_gc(self, tracker):
        """Test force GC"""
        tracker.start()
        # Create some objects
        _ = [{"data": i} for i in range(100)]

        tracker.force_gc()

        assert tracker.stats.gc_runs == 1

        tracker.stop()

    def test_get_stats(self, tracker):
        """Test get stats"""
        tracker.start()
        tracker.take_snapshot()
        stats = tracker.get_stats()

        assert "initial_mb" in stats
        assert "current_mb" in stats
        assert "peak_mb" in stats

        tracker.stop()

    def test_clear_snapshots(self, tracker):
        """Test clear snapshots"""
        tracker.start()
        tracker.take_snapshot()
        tracker.take_snapshot()

        assert len(tracker.get_snapshots()) == 2

        tracker.clear_snapshots()
        assert len(tracker.get_snapshots()) == 0

        tracker.stop()


class TestMemoryOptimizer:
    """Test MemoryOptimizer"""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer"""
        return MemoryOptimizer(threshold_mb=1.0)

    def test_optimizer_init(self, optimizer):
        """Test optimizer init"""
        assert optimizer.threshold_mb == 1.0
        assert optimizer._auto_gc_enabled is False

    def test_start_stop_auto_gc(self, optimizer):
        """Test auto GC"""
        optimizer.start_auto_gc()
        assert optimizer._auto_gc_enabled is True

        optimizer.stop_auto_gc()
        assert optimizer._auto_gc_enabled is False

    def test_optimize_dataclass(self, optimizer):
        """Test dataclass optimization"""
        @dataclass
        class TestData:
            name: str
            values: list

        data = TestData("test", [1, 2, 3])
        result = optimizer.optimize_dataclass(data)

        # Should be converted to tuple
        assert isinstance(result, tuple)

    def test_estimate_size(self, optimizer):
        """Test size estimation"""
        obj = {"key": "value"}
        size = optimizer.estimate_size(obj)
        assert size > 0

    def test_clear_circular_refs(self, optimizer):
        """Test clear circular refs"""
        class TestObj:
            pass

        obj = TestObj()
        obj.data = list(range(2000))

        optimizer.clear_circular_refs(obj)
        # Large list should be cleared
        assert obj.data is None
