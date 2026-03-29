"""
Stages - Pipeline stages and execution
Этапы конвейера и выполнения
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StageStatus(Enum):
    """Статус этапа"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class StageResult:
    """Результат этапа"""
    status: StageStatus
    output: Any = None
    error: str = None
    duration: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class Stage:
    """Этап конвейера"""
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: StageStatus = StageStatus.PENDING
    result: StageResult = None
    dependencies: list[str] = field(default_factory=list)
    timeout: float = None
    retry_count: int = 0
    retry_delay: float = 1.0
    created_at: float = field(default_factory=time.time)
    started_at: float = None
    completed_at: float = None

    def is_completed(self) -> bool:
        """Завершён?"""
        return self.status in (StageStatus.COMPLETED, StageStatus.SKIPPED)

    def is_failed(self) -> bool:
        """Ошибка?"""
        return self.status == StageStatus.FAILED

    def is_running(self) -> bool:
        """Выполняется?"""
        return self.status == StageStatus.RUNNING


class Pipeline:
    """Конвейер этапов"""

    def __init__(self, name: str = "default"):
        self.name = name
        self._stages: dict[str, Stage] = {}
        self._execution_order: list[str] = []

    def add_stage(
        self,
        name: str,
        func: Callable,
        dependencies: list[str] = None,
        args: tuple = None,
        kwargs: dict = None,
        timeout: float = None,
        retry_count: int = 0,
        retry_delay: float = 1.0,
    ) -> "Pipeline":
        """Добавление этапа"""
        stage = Stage(
            name=name,
            func=func,
            dependencies=dependencies or [],
            args=args or (),
            kwargs=kwargs or {},
            timeout=timeout,
            retry_count=retry_count,
            retry_delay=retry_delay,
        )
        self._stages[name] = stage
        return self

    def get_stage(self, name: str) -> Stage | None:
        """Получение этапа"""
        return self._stages.get(name)

    def remove_stage(self, name: str) -> bool:
        """Удаление этапа"""
        if name in self._stages:
            del self._stages[name]
            return True
        return False

    def get_ready_stages(self) -> list[str]:
        """Получение готовых к выполнению этапов"""
        ready = []
        for name, stage in self._stages.items():
            if stage.status != StageStatus.PENDING:
                continue

            # Check dependencies
            deps_met = all(
                self._stages.get(dep).is_completed()
                for dep in stage.dependencies
                if dep in self._stages
            )

            if deps_met:
                ready.append(name)

        return ready

    def _topological_sort(self) -> bool:
        """Топологическая сортировка"""
        in_degree = {name: len(stage.dependencies) for name, stage in self._stages.items()}

        for deps in self._stages.values():
            for dep in deps.dependencies:
                if dep not in in_degree:
                    return False

        queue = [name for name, degree in in_degree.items() if degree == 0]
        self._execution_order = []

        while queue:
            current = queue.pop(0)
            self._execution_order.append(current)

            for name, stage in self._stages.items():
                if current in stage.dependencies:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)

        return len(self._execution_order) == len(self._stages)

    def execute(self, context: dict = None) -> dict[str, StageResult]:
        """Выполнение конвейера"""
        if not self._topological_sort():
            raise ValueError("Circular dependency detected")

        results = {}
        context = context or {}

        for stage_name in self._execution_order:
            stage = self._stages[stage_name]

            # Check if already completed or failed
            if stage.is_completed() or stage.is_failed():
                continue

            # Execute stage
            stage.status = StageStatus.RUNNING
            stage.started_at = time.time()

            try:
                result = stage.func(*stage.args, **stage.kwargs, **context)

                # Handle async
                if asyncio.iscoroutine(result):
                    result = asyncio.run(result)

                stage.result = StageResult(
                    status=StageStatus.COMPLETED,
                    output=result,
                    duration=time.time() - stage.started_at,
                )
                stage.status = StageStatus.COMPLETED

            except Exception as e:
                stage.result = StageResult(
                    status=StageStatus.FAILED,
                    error=str(e),
                    duration=time.time() - stage.started_at,
                )
                stage.status = StageStatus.FAILED

            stage.completed_at = time.time()
            results[stage_name] = stage.result

        return results

    async def execute_async(self, context: dict = None) -> dict[str, StageResult]:
        """Асинхронное выполнение"""
        if not self._topological_sort():
            raise ValueError("Circular dependency detected")

        results = {}
        context = context or {}

        for stage_name in self._execution_order:
            stage = self._stages[stage_name]

            if stage.is_completed() or stage.is_failed():
                continue

            stage.status = StageStatus.RUNNING
            stage.started_at = time.time()

            try:
                result = stage.func(*stage.args, **stage.kwargs, **context)

                if asyncio.iscoroutinefunction(stage.func):
                    result = await result

                stage.result = StageResult(
                    status=StageStatus.COMPLETED,
                    output=result,
                    duration=time.time() - stage.started_at,
                )
                stage.status = StageStatus.COMPLETED

            except Exception as e:
                stage.result = StageResult(
                    status=StageStatus.FAILED,
                    error=str(e),
                    duration=time.time() - stage.started_at,
                )
                stage.status = StageStatus.FAILED

            stage.completed_at = time.time()
            results[stage_name] = stage.result

        return results

    def list_stages(self) -> list[str]:
        """Список этапов"""
        return list(self._stages.keys())

    def get_status_summary(self) -> dict:
        """Сводка статусов"""
        summary = {
            "total": len(self._stages),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
        }

        for stage in self._stages.values():
            summary[stage.status.value] += 1

        return summary


class StageBuilder:
    """Строитель этапов"""

    def __init__(self, pipeline: Pipeline):
        self._pipeline = pipeline

    def stage(self, name: str, func: Callable, **kwargs) -> "StageBuilder":
        """Добавление этапа"""
        self._pipeline.add_stage(name, func, **kwargs)
        return self

    def then(self, name: str, func: Callable, **kwargs) -> "StageBuilder":
        """Добавление этапа с зависимостью от предыдущего"""
        stages = self._pipeline.list_stages()
        last_stage = stages[-1] if stages else None

        deps = [last_stage] if last_stage else []
        self._pipeline.add_stage(name, func, dependencies=deps, **kwargs)
        return self

    def build(self) -> Pipeline:
        """Построение"""
        return self._pipeline


def create_pipeline(name: str = "default") -> Pipeline:
    """Создание конвейера"""
    return Pipeline(name)


def create_stage_builder(name: str = "default") -> StageBuilder:
    """Создание строителя"""
    return StageBuilder(create_pipeline(name))
