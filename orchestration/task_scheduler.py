"""
Task scheduler
Планировщик задач с поддержкой cron и интервалов
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("orchestration.scheduler")


@dataclass
class ScheduledTask:
    """Запланированная задача"""
    name: str
    func: Callable
    interval_seconds: float = None
    cron_expression: str = None
    enabled: bool = True
    last_run: float = None
    next_run: float = None
    run_count: int = 0
    error_count: int = 0


class TaskScheduler:
    """
    Планировщик задач
    """

    def __init__(self):
        self._tasks: dict[str, ScheduledTask] = {}
        self._running = False
        self._task: asyncio.Task | None = None

    def add_interval(
        self,
        name: str,
        func: Callable,
        interval_seconds: float,
    ):
        """Добавление задачи с интервалом"""
        task = ScheduledTask(
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            next_run=datetime.now().timestamp(),
        )
        self._tasks[name] = task
        logger.info(f"Added interval task: {name} every {interval_seconds}s")

    def add_cron(self, name: str, func: Callable, cron: str):
        """Добавление cron задачи"""
        # Simple cron parsing (only supports basic expressions)
        # Format: "minute hour day month day_of_week"
        parts = cron.split()
        if len(parts) >= 1:
            # For simplicity, treat first part as seconds interval
            try:
                interval = int(parts[0]) * 60  # minutes to seconds
            except ValueError:
                interval = 60  # default 1 minute
        else:
            interval = 60

        task = ScheduledTask(
            name=name,
            func=func,
            cron_expression=cron,
            interval_seconds=interval,
            next_run=datetime.now().timestamp(),
        )
        self._tasks[name] = task
        logger.info(f"Added cron task: {name} ({cron})")

    def remove(self, name: str):
        """Удаление задачи"""
        if name in self._tasks:
            del self._tasks[name]
            logger.info(f"Removed task: {name}")

    def enable(self, name: str):
        """Включение задачи"""
        if name in self._tasks:
            self._tasks[name].enabled = True

    def disable(self, name: str):
        """Отключение задачи"""
        if name in self._tasks:
            self._tasks[name].enabled = False

    async def start(self):
        """Запуск планировщика"""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Task scheduler started")

    async def stop(self):
        """Остановка планировщика"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Task scheduler stopped")

    async def _run_loop(self):
        """Основной цикл"""
        while self._running:
            try:
                now = datetime.now().timestamp()

                for task in self._tasks.values():
                    if not task.enabled:
                        continue

                    if task.next_run and now >= task.next_run:
                        await self._execute_task(task)

                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

    async def _execute_task(self, task: ScheduledTask):
        """Выполнение задачи"""
        try:
            if asyncio.iscoroutinefunction(task.func):
                await task.func()
            else:
                task.func()

            task.last_run = datetime.now().timestamp()
            task.run_count += 1
            task.next_run = task.last_run + task.interval_seconds
            logger.debug(f"Task completed: {task.name}")

        except Exception as e:
            task.error_count += 1
            logger.error(f"Task error {task.name}: {e}")

    def get_status(self) -> dict:
        """Получение статуса"""
        return {
            "running": self._running,
            "tasks": {
                name: {
                    "enabled": t.enabled,
                    "interval": t.interval_seconds,
                    "run_count": t.run_count,
                    "error_count": t.error_count,
                    "next_run": t.next_run,
                }
                for name, t in self._tasks.items()
            },
        }


# Singleton
_scheduler: TaskScheduler | None = None


def get_scheduler() -> TaskScheduler:
    """Получение планировщика"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
