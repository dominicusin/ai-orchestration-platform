"""
Data sources for input
Источники данных для ввода
"""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import Any

logger = logging.getLogger("orchestration.sources")


class Source(ABC):
    """Базовый класс источника"""

    @abstractmethod
    def read(self) -> Any:
        """Чтение данных"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Закрытие источника"""
        pass


class FileSource(Source):
    """Источник из файла"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file = None

    def __enter__(self):
        self.file = open(self.file_path, encoding="utf-8")
        return self

    def __exit__(self, *args):
        self.close()

    def read(self) -> str:
        if self.file is None:
            self.file = open(self.file_path, encoding="utf-8")
        return self.file.read()

    def read_lines(self) -> Iterator[str]:
        """Чтение построчно"""
        with open(self.file_path, encoding="utf-8") as f:
            for line in f:
                yield line.rstrip("\n")

    def close(self) -> None:
        if self.file:
            self.file.close()
            self.file = None


class JSONFileSource(Source):
    """Источник JSON из файла"""

    def __init__(self, file_path: str, lines: bool = False):
        self.file_path = Path(file_path)
        self.lines = lines

    def read(self) -> Any:
        with open(self.file_path, encoding="utf-8") as f:
            if self.lines:
                return [json.loads(line) for line in f]
            return json.load(f)

    def close(self) -> None:
        pass


class StringSource(Source):
    """Источник из строки"""

    def __init__(self, data: str):
        self.data = data

    def read(self) -> str:
        return self.data

    def close(self) -> None:
        pass


class ListSource(Source):
    """Источник из списка"""

    def __init__(self, data: list):
        self.data = data

    def read(self) -> list:
        return self.data

    def close(self) -> None:
        pass


class DictSource(Source):
    """Источник из словаря"""

    def __init__(self, data: dict):
        self.data = data

    def read(self) -> dict:
        return self.data

    def close(self) -> None:
        pass


class GeneratorSource(Source):
    """Источник из генератора"""

    def __init__(self, gen: Iterator):
        self.gen = gen

    def read(self) -> Any:
        try:
            return next(self.gen)
        except StopIteration:
            return None

    def read_all(self) -> list:
        return list(self.gen)

    def close(self) -> None:
        pass


class CallbackSource(Source):
    """Источник с callback функцией"""

    def __init__(self, callback: callable):
        self.callback = callback

    def read(self) -> Any:
        return self.callback()

    def close(self) -> None:
        pass


class MultiSource(Source):
    """Источник объединяющий несколько"""

    def __init__(self, *sources: Source):
        self.sources = list(sources)
        self._index = 0

    def read(self) -> Any:
        if self._index >= len(self.sources):
            return None
        result = self.sources[self._index].read()
        self._index += 1
        return result

    def read_all(self) -> list:
        results = []
        for source in self.sources:
            results.append(source.read())
        return results

    def reset(self):
        """Сброс индексов"""
        self._index = 0
        for source in self.sources:
            if hasattr(source, "reset"):
                source.reset()

    def close(self) -> None:
        for source in self.sources:
            source.close()


# Factory functions

def get_source(source_type: str, **kwargs) -> Source:
    """Получение источника по типу"""
    sources = {
        "file": FileSource,
        "json_file": JSONFileSource,
        "string": StringSource,
        "list": ListSource,
        "dict": DictSource,
    }

    if source_type not in sources:
        raise ValueError(f"Unknown source type: {source_type}")

    return sources[source_type](**kwargs)


def create_file_source(path: str, **kwargs) -> FileSource:
    """Создание файлового источника"""
    return FileSource(path, **kwargs)


def create_json_source(path: str, **kwargs) -> JSONFileSource:
    """Создание JSON источника"""
    return JSONFileSource(path, **kwargs)


def create_multi_source(*sources: Source) -> MultiSource:
    """Создание мульти источника"""
    return MultiSource(*sources)
