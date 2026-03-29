"""
Data sinks for output
Стки данных для вывода
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger("orchestration.sinks")


class Sink(ABC):
    """Базовый класс стока"""

    @abstractmethod
    def write(self, data: Any) -> None:
        """Запись данных"""

    @abstractmethod
    def flush(self) -> None:
        """Сброс буфера"""

    @abstractmethod
    def close(self) -> None:
        """Закрытие стока"""


class FileSink(Sink):
    """Сток в файл"""

    def __init__(self, file_path: str, mode: str = "a"):
        self.file_path = Path(file_path)
        self.mode = mode
        self.file = None

    def __enter__(self):
        self.file = open(self.file_path, self.mode, encoding="utf-8")
        return self

    def __exit__(self, *args):
        self.close()

    def write(self, data: Any) -> None:
        if self.file is None:
            self.file = open(self.file_path, self.mode, encoding="utf-8")

        if isinstance(data, (dict, list)):
            self.file.write(json.dumps(data, ensure_ascii=False))
        else:
            self.file.write(str(data))
        self.file.write("\n")

    def flush(self) -> None:
        if self.file:
            self.file.flush()

    def close(self) -> None:
        if self.file:
            self.file.close()
            self.file = None


class JSONFileSink(Sink):
    """Сток JSON в файл (построчно)"""

    def __init__(self, file_path: str, indent: int = 2):
        self.file_path = Path(file_path)
        self.indent = indent
        self.file = None

    def __enter__(self):
        self.file = open(self.file_path, "w", encoding="utf-8")
        return self

    def __exit__(self, *args):
        self.close()

    def write(self, data: Any) -> None:
        if self.file is None:
            self.file = open(self.file_path, "w", encoding="utf-8")

        line = json.dumps(data, ensure_ascii=False, indent=self.indent)
        self.file.write(line)
        self.file.write("\n")

    def flush(self) -> None:
        if self.file:
            self.file.flush()

    def close(self) -> None:
        if self.file:
            self.file.close()
            self.file = None


class ConsoleSink(Sink):
    """Сток в консоль"""

    def __init__(self, format_json: bool = False):
        self.format_json = format_json

    def write(self, data: Any) -> None:
        if self.format_json or isinstance(data, (dict, list)):
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class ListSink(Sink):
    """Сток в список (для тестирования)"""

    def __init__(self):
        self.data: list = []

    def write(self, data: Any) -> None:
        self.data.append(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

    def clear(self) -> None:
        self.data.clear()

    def get_all(self) -> list:
        return self.data


class NullSink(Sink):
    """Сток в никуда ( discard )"""

    def write(self, data: Any) -> None:
        pass

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class CallbackSink(Sink):
    """Сток с callback функцией"""

    def __init__(self, callback: callable):
        self.callback = callback

    def write(self, data: Any) -> None:
        self.callback(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class MultiSink(Sink):
    """Сток с несколькими получателями"""

    def __init__(self, *sinks: Sink):
        self.sinks = list(sinks)

    def add_sink(self, sink: Sink):
        """Добавление стока"""
        self.sinks.append(sink)

    def write(self, data: Any) -> None:
        for sink in self.sinks:
            sink.write(data)

    def flush(self) -> None:
        for sink in self.sinks:
            sink.flush()

    def close(self) -> None:
        for sink in self.sinks:
            sink.close()


# Factory functions

def get_sink(sink_type: str, **kwargs) -> Sink:
    """Получение стока по типу"""
    sinks = {
        "file": FileSink,
        "json_file": JSONFileSink,
        "console": ConsoleSink,
        "list": ListSink,
        "null": NullSink,
    }

    if sink_type not in sinks:
        raise ValueError(f"Unknown sink type: {sink_type}")

    return sinks[sink_type](**kwargs)


def create_file_sink(path: str, **kwargs) -> FileSink:
    """Создание файлового стока"""
    return FileSink(path, **kwargs)


def create_console_sink(**kwargs) -> ConsoleSink:
    """Создание консольного стока"""
    return ConsoleSink(**kwargs)


def create_multi_sink(*sinks: Sink) -> MultiSink:
    """Создание мульти стока"""
    return MultiSink(*sinks)
