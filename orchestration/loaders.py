"""
Loaders for various data sources
Загрузчики данных из различных источников
"""

import csv
import json
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from pathlib import Path
from typing import Any


class Loader:
    """Базовый класс загрузчика"""

    def load(self, path: str) -> Any:
        """Загрузка данных"""
        raise NotImplementedError


class JSONLoader(Loader):
    """Загрузка JSON"""

    def load(self, path: str) -> Any:
        """Загрузка из JSON файла"""
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def load_lines(self, path: str) -> Iterator[dict]:
        """Загрузка JSON строк (JSONL)"""
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


class CSVLoader(Loader):
    """Загрузка CSV"""

    def __init__(self, delimiter: str = ",", has_header: bool = True):
        self.delimiter = delimiter
        self.has_header = has_header

    def load(self, path: str) -> list:
        """Загрузка из CSV файла"""
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter) if self.has_header else csv.reader(f, delimiter=self.delimiter)
            return list(reader)


class XMLLoader(Loader):
    """Загрузка XML"""

    def __init__(self, root: str = "root", item: str = "item"):
        self.root = root
        self.item = item

    def load(self, path: str) -> list:
        """Загрузка из XML файла"""
        tree = ET.parse(path)
        root = tree.getroot()

        results = []
        for elem in root.findall(self.item):
            item = {}
            for child in elem:
                item[child.tag] = child.text
            if not item:
                item = elem.text
            results.append(item)

        return results


class TextLoader(Loader):
    """Загрузка текста"""

    def load(self, path: str) -> str:
        """Загрузка текстового файла"""
        with open(path, encoding="utf-8") as f:
            return f.read()

    def load_lines(self, path: str) -> Iterator[str]:
        """Загрузка строк"""
        with open(path, encoding="utf-8") as f:
            for line in f:
                yield line.rstrip("\n")


class DirectoryLoader(Loader):
    """Загрузка файлов из директории"""

    def __init__(self, pattern: str = "*", recursive: bool = True):
        self.pattern = pattern
        self.recursive = recursive

    def load(self, path: str) -> list:
        """Загрузка списка файлов"""
        dir_path = Path(path)
        if self.recursive:
            files = dir_path.rglob(self.pattern)
        else:
            files = dir_path.glob(self.pattern)
        return [str(f) for f in files if f.is_file()]


class GlobLoader(Loader):
    """Загрузка по glob паттерну"""

    def __init__(self, pattern: str):
        self.pattern = pattern

    def load(self, path: str) -> list:
        """Загрузка файлов по паттерну"""
        from pathlib import Path
        base = Path(path)
        files = base.glob(self.pattern)
        return [str(f) for f in files if f.is_file()]


# Factory functions

def get_loader(format: str, **kwargs) -> Loader:
    """Получение загрузчика по формату"""
    loaders = {
        "json": JSONLoader,
        "csv": CSVLoader,
        "xml": XMLLoader,
        "text": TextLoader,
        "directory": DirectoryLoader,
        "glob": GlobLoader,
    }

    if format not in loaders:
        raise ValueError(f"Unknown format: {format}")

    return loaders[format](**kwargs)


def load_json(path: str, **kwargs) -> Any:
    """Загрузка JSON"""
    return JSONLoader(**kwargs).load(path)


def load_csv(path: str, **kwargs) -> list:
    """Загрузка CSV"""
    return CSVLoader(**kwargs).load(path)


def load_xml(path: str, **kwargs) -> list:
    """Загрузка XML"""
    return XMLLoader(**kwargs).load(path)


def load_text(path: str, **kwargs) -> str:
    """Загрузка текста"""
    return TextLoader(**kwargs).load(path)
