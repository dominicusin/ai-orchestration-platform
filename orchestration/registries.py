"""
Registries for storing and finding objects
Реестры для хранения и поиска объектов
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RegistryEntry:
    """Запись реестра"""
    name: str
    obj: Any
    metadata: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class Registry:
    """Базовый реестр"""

    def __init__(self, name: str = "default"):
        self.name = name
        self._entries: dict[str, RegistryEntry] = {}

    def register(self, name: str, obj: Any, tags: list[str] = None, metadata: dict = None):
        """Регистрация объекта"""
        entry = RegistryEntry(
            name=name,
            obj=obj,
            tags=tags or [],
            metadata=metadata or {},
        )
        self._entries[name] = entry

    def unregister(self, name: str) -> bool:
        """Удаление регистрации"""
        if name in self._entries:
            del self._entries[name]
            return True
        return False

    def get(self, name: str) -> Any | None:
        """Получение объекта по имени"""
        entry = self._entries.get(name)
        return entry.obj if entry else None

    def get_entry(self, name: str) -> RegistryEntry | None:
        """Получение записи"""
        return self._entries.get(name)

    def list_names(self) -> list[str]:
        """Список всех имён"""
        return list(self._entries.keys())

    def list_objects(self) -> list[Any]:
        """Список всех объектов"""
        return [e.obj for e in self._entries.values()]

    def list_entries(self) -> list[RegistryEntry]:
        """Список всех записей"""
        return list(self._entries.values())

    def find_by_tag(self, tag: str) -> list[Any]:
        """Поиск по тегу"""
        return [
            entry.obj for entry in self._entries.values()
            if tag in entry.tags
        ]

    def find_by_metadata(self, key: str, value: Any) -> list[Any]:
        """Поиск по метаданным"""
        return [
            entry.obj for entry in self._entries.values()
            if entry.metadata.get(key) == value
        ]

    def exists(self, name: str) -> bool:
        """Проверка существования"""
        return name in self._entries

    def count(self) -> int:
        """Количество записей"""
        return len(self._entries)

    def clear(self):
        """Очистка реестра"""
        self._entries.clear()

    def filter(self, predicate: Callable[[RegistryEntry], bool]) -> list[Any]:
        """Фильтрация по предикату"""
        return [
            entry.obj for entry in self._entries.values()
            if predicate(entry)
        ]


class TypeRegistry(Registry):
    """Реестр с типизацией"""

    def register(self, name: str, obj: Any, obj_type: type = None, tags: list[str] = None, metadata: dict = None):
        """Регистрация с типом"""
        if obj_type is None:
            obj_type = type(obj)

        metadata = metadata or {}
        metadata["type"] = obj_type.__name__

        super().register(name, obj, tags, metadata)

    def get_by_type(self, obj_type: type) -> list[Any]:
        """Получение по типу"""
        return [
            entry.obj for entry in self._entries.values()
            if entry.metadata.get("type") == obj_type.__name__
        ]


class HierarchicalRegistry(Registry):
    """Иерархический реестр с родителями"""

    def __init__(self, name: str = "default", parent: "HierarchicalRegistry" = None):
        super().__init__(name)
        self.parent = parent

    def get(self, name: str) -> Any | None:
        """Получение с учётом иерархии"""
        entry = self._entries.get(name)
        if entry:
            return entry.obj

        if self.parent:
            return self.parent.get(name)

        return None

    def find_by_tag(self, tag: str) -> list[Any]:
        """Поиск по тегу с учётом иерархии"""
        results = super().find_by_tag(tag)

        if self.parent:
            parent_results = self.parent.find_by_tag(tag)
            results.extend(parent_results)

        return results


class LazyRegistry(Registry):
    """Ленивый реестр с отложенной загрузкой"""

    def __init__(self, name: str = "default"):
        super().__init__(name)
        self._factories: dict[str, Callable] = {}

    def register_factory(self, name: str, factory: Callable, tags: list[str] = None):
        """Регистрация фабрики"""
        self._factories[name] = factory
        entry = RegistryEntry(
            name=name,
            obj=None,
            tags=tags or [],
            metadata={"lazy": True},
        )
        self._entries[name] = entry

    def get(self, name: str) -> Any:
        """Получение с созданием при первом доступе"""
        entry = self._entries.get(name)
        if not entry:
            return None

        if entry.obj is None and name in self._factories:
            entry.obj = self._factories[name]()

        return entry.obj


# Singleton
_default_registry: Registry | None = None


def get_registry(name: str = "default") -> Registry:
    """Получение реестра"""
    global _default_registry
    if _default_registry is None:
        _default_registry = Registry(name)
    return _default_registry


def register(name: str, obj: Any, tags: list[str] = None, metadata: dict = None):
    """Быстрая регистрация"""
    get_registry().register(name, obj, tags, metadata)


def get(name: str) -> Any | None:
    """Быстрое получение"""
    return get_registry().get(name)
