"""Tests for Task Scheduler"""

import asyncio

import pytest

from orchestration.task_scheduler import (
    ScheduledTask,
    TaskScheduler,
    get_scheduler,
)


class TestScheduledTask:
    """Test ScheduledTask"""

    def test_creation(self):
        """Test creation"""
        def test_func():
            pass

        task = ScheduledTask(
            name="test",
            func=test_func,
            interval_seconds=60.0,
        )
        assert task.name == "test"
        assert task.interval_seconds == 60.0
        assert task.enabled is True


class TestTaskScheduler:
    """Test TaskScheduler"""

    @pytest.fixture
    def scheduler(self):
        """Create scheduler"""
        return TaskScheduler()

    def test_creation(self, scheduler):
        """Test creation"""
        assert scheduler is not None
        assert scheduler._running is False

    def test_add_interval(self, scheduler):
        """Test add interval task"""
        def test_func():
            pass

        scheduler.add_interval("test_task", test_func, 60.0)
        assert "test_task" in scheduler._tasks
        assert scheduler._tasks["test_task"].interval_seconds == 60.0

    def test_add_cron(self, scheduler):
        """Test add cron task"""
        def test_func():
            pass

        scheduler.add_cron("cron_task", test_func, "5 * * * *")
        assert "cron_task" in scheduler._tasks

    def test_remove(self, scheduler):
        """Test remove task"""
        def test_func():
            pass

        scheduler.add_interval("test_task", test_func, 60.0)
        scheduler.remove("test_task")
        assert "test_task" not in scheduler._tasks

    def test_enable_disable(self, scheduler):
        """Test enable/disable"""
        def test_func():
            pass

        scheduler.add_interval("test_task", test_func, 60.0)
        assert scheduler._tasks["test_task"].enabled is True

        scheduler.disable("test_task")
        assert scheduler._tasks["test_task"].enabled is False

        scheduler.enable("test_task")
        assert scheduler._tasks["test_task"].enabled is True

    @pytest.mark.asyncio
    async def test_start_stop(self, scheduler):
        """Test start and stop"""
        await scheduler.start()
        assert scheduler._running is True

        await scheduler.stop()
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_execute_task(self, scheduler):
        """Test task execution"""
        results = []

        def test_func():
            results.append("executed")

        scheduler.add_interval("test_task", test_func, 0.1)
        task = scheduler._tasks["test_task"]

        await scheduler._execute_task(task)
        await asyncio.sleep(0.05)

        assert len(results) == 1
        assert task.run_count == 1

    def test_get_status(self, scheduler):
        """Test get status"""
        def test_func():
            pass

        scheduler.add_interval("test_task", test_func, 60.0)

        status = scheduler.get_status()
        assert "running" in status
        assert "tasks" in status
        assert "test_task" in status["tasks"]


class TestSchedulerSingleton:
    """Test singleton"""

    def test_singleton(self):
        """Test singleton"""
        s1 = get_scheduler()
        s2 = get_scheduler()
        assert s1 is s2
