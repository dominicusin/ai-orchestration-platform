"""
Pipelines - Data processing pipelines
Конвейеры обработки данных
"""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from typing import Any, Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class PipelineStage(ABC, Generic[T, R]):
    """Базовый класс этапа конвейера"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process(self, data: T) -> R:
        """Обработка данных"""
        pass

    async def process_async(self, data: T) -> R:
        """Асинхронная обработка"""
        return self.process(data)


class TransformStage(PipelineStage[T, R]):
    """Этап трансформации"""

    def __init__(self, name: str, transform: Callable[[T], R]):
        super().__init__(name)
        self.transform = transform

    def process(self, data: T) -> R:
        return self.transform(data)


class FilterStage(PipelineStage[T, T]):
    """Этап фильтрации"""

    def __init__(self, name: str, predicate: Callable[[T], bool]):
        super().__init__(name)
        self.predicate = predicate

    def process(self, data: T) -> T:
        if self.predicate(data):
            return data
        raise StopIteration("Filtered out")


class MapStage(PipelineStage[T, R]):
    """Этап отображения (map)"""

    def __init__(self, name: str, mapper: Callable[[T], R]):
        super().__init__(name)
        self.mapper = mapper

    def process(self, data: T) -> R:
        return self.mapper(data)


class FlatMapStage(PipelineStage[T, R]):
    """Этап плоского отображения (flatMap)"""

    def __init__(self, name: str, flat_mapper: Callable[[T], list[R]]):
        super().__init__(name)
        self.flat_mapper = flat_mapper

    def process(self, data: T) -> list[R]:
        return self.flat_mapper(data)


class ReduceStage(PipelineStage[list[T], R]):
    """Этап свертки (reduce)"""

    def __init__(self, name: str, reducer: Callable[[Any, T], R], initial: R = None):
        super().__init__(name)
        self.reducer = reducer
        self.initial = initial

    def process(self, data: list[T]) -> R:
        if not data:
            return self.initial
        if self.initial is not None:
            result = self.initial
            for item in data:
                result = self.reducer(result, item)
        else:
            result = data[0]
            for item in data[1:]:
                result = self.reducer(result, item)
        return result


class Pipeline(Generic[T]):
    """Конвейер обработки данных"""

    def __init__(self, name: str = "default"):
        self.name = name
        self._stages: list[PipelineStage] = []
        self._error_handler: Callable | None = None

    def add_stage(self, stage: PipelineStage) -> "Pipeline":
        """Добавление этапа"""
        self._stages.append(stage)
        return self

    def transform(self, name: str, transform: Callable) -> "Pipeline":
        """Добавление трансформации"""
        return self.add_stage(TransformStage(name, transform))

    def filter(self, name: str, predicate: Callable) -> "Pipeline":
        """Добавление фильтра"""
        return self.add_stage(FilterStage(name, predicate))

    def map(self, name: str, mapper: Callable) -> "Pipeline":
        """Добавление map"""
        return self.add_stage(MapStage(name, mapper))

    def flat_map(self, name: str, flat_mapper: Callable) -> "Pipeline":
        """Добавление flatMap"""
        return self.add_stage(FlatMapStage(name, flat_mapper))

    def reduce(self, name: str, reducer: Callable, initial: Any = None) -> "Pipeline":
        """Добавление reduce"""
        return self.add_stage(ReduceStage(name, reducer, initial))

    def on_error(self, handler: Callable) -> "Pipeline":
        """Обработчик ошибок"""
        self._error_handler = handler
        return self

    def process(self, data: T) -> Any:
        """Обработка данных"""
        result = data

        for stage in self._stages:
            try:
                result = stage.process(result)
            except StopIteration:
                return None
            except Exception as e:
                if self._error_handler:
                    self._error_handler(e, stage)
                else:
                    raise

        return result

    def process_batch(self, data: list[T]) -> list[Any]:
        """Обработка батча"""
        results = []
        for item in data:
            try:
                result = self.process(item)
                if result is not None:
                    results.append(result)
            except Exception:
                pass
        return results

    def process_stream(self, data: Iterator[T]) -> Iterator[Any]:
        """Обработка потока"""
        for item in data:
            try:
                result = self.process(item)
                if result is not None:
                    yield result
            except Exception:
                pass


class AsyncPipeline(Generic[T]):
    """Асинхронный конвейер"""

    def __init__(self, name: str = "default"):
        self.name = name
        self._stages: list[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> "AsyncPipeline":
        self._stages.append(stage)
        return self

    async def process(self, data: T) -> Any:
        """Асинхронная обработка"""
        result = data

        for stage in self._stages:
            if asyncio.iscoroutinefunction(stage.process):
                result = await stage.process_async(result)
            else:
                result = stage.process(result)

        return result

    async def process_batch(self, data: list[T]) -> list[Any]:
        """Обработка батча"""
        tasks = [self.process(item) for item in data]
        return await asyncio.gather(*tasks, return_exceptions=True)


class PipelineBuilder:
    """Строитель конвейера"""

    def __init__(self, name: str = "default"):
        self._pipeline = Pipeline(name)

    def transform(self, name: str, transform: Callable) -> "PipelineBuilder":
        self._pipeline.transform(name, transform)
        return self

    def filter(self, name: str, predicate: Callable) -> "PipelineBuilder":
        self._pipeline.filter(name, predicate)
        return self

    def map(self, name: str, mapper: Callable) -> "PipelineBuilder":
        self._pipeline.map(name, mapper)
        return self

    def build(self) -> Pipeline:
        return self._pipeline


def create_pipeline(name: str = "default") -> Pipeline:
    """Создание конвейера"""
    return Pipeline(name)


def create_async_pipeline(name: str = "default") -> AsyncPipeline:
    """Создание асинхронного конвейера"""
    return AsyncPipeline(name)
