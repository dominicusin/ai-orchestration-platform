"""
Filters for data processing
Фильтры для обработки данных
"""

from collections.abc import Callable
from typing import Any


class Filter:
    """Базовый класс фильтра"""

    def apply(self, data: Any) -> Any:
        """Применение фильтра"""
        raise NotImplementedError


class LambdaFilter(Filter):
    """Фильтр на основе lambda функции"""

    def __init__(self, func: Callable[[Any], bool]):
        self.func = func

    def apply(self, data: Any) -> Any:
        if isinstance(data, list):
            return [item for item in data if self.func(item)]
        return data if self.func(data) else None


class KeyFilter(Filter):
    """Фильтр по ключу"""

    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value

    def apply(self, data: Any) -> Any:
        if isinstance(data, list):
            return [
                item for item in data
                if isinstance(item, dict) and item.get(self.key) == self.value
            ]
        if isinstance(data, dict):
            return data if data.get(self.key) == self.value else None
        return data


class RangeFilter(Filter):
    """Фильтр по диапазону"""

    def __init__(self, min_val: float = None, max_val: float = None, key: str = None):
        self.min_val = min_val
        self.max_val = max_val
        self.key = key

    def apply(self, data: Any) -> Any:
        def in_range(item):
            val = item.get(self.key, item) if isinstance(item, dict) and self.key else item
            try:
                num = float(val)
                if self.min_val is not None and num < self.min_val:
                    return False
                if self.max_val is not None and num > self.max_val:
                    return False
                return True
            except (ValueError, TypeError):
                return False

        if isinstance(data, list):
            return [item for item in data if in_range(item)]
        return data if in_range(data) else None


class RegexFilter(Filter):
    """Фильтр по регулярному выражению"""

    def __init__(self, pattern: str, key: str = None):
        import re
        self.pattern = re.compile(pattern)
        self.key = key

    def apply(self, data: Any) -> Any:
        def matches(item):
            val = item.get(self.key, item) if isinstance(item, dict) and self.key else item
            return bool(self.pattern.search(str(val)))

        if isinstance(data, list):
            return [item for item in data if matches(item)]
        return data if matches(data) else None


class TypeFilter(Filter):
    """Фильтр по типу"""

    def __init__(self, *types: type):
        self.types = types

    def apply(self, data: Any) -> Any:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, self.types)]
        return data if isinstance(data, self.types) else None


class CompositeFilter(Filter):
    """Композитный фильтр"""

    def __init__(self, *filters: Filter, mode: str = "and"):
        self.filters = filters
        self.mode = mode  # "and" or "or"

    def apply(self, data: Any) -> Any:
        if not self.filters:
            return data

        if self.mode == "and":
            result = data
            for f in self.filters:
                result = f.apply(result)
            return result
        else:  # or
            result = []
            for f in self.filters:
                filtered = f.apply(data)
                if filtered:
                    result.extend(filtered if isinstance(filtered, list) else [filtered])
            return list(set(result)) if result else data

    def add(self, filter_: Filter):
        """Добавление фильтра"""
        self.filters = (*self.filters, filter_)


class DedupeFilter(Filter):
    """Фильтр удаления дубликатов"""

    def __init__(self, key: str = None):
        self.key = key

    def apply(self, data: Any) -> Any:
        if not isinstance(data, list):
            return data

        seen = set()
        result = []

        for item in data:
            val = item.get(self.key) if isinstance(item, dict) and self.key else item
            if val not in seen:
                seen.add(val)
                result.append(item)

        return result


class SortFilter(Filter):
    """Фильтр сортировки"""

    def __init__(self, key: str = None, reverse: bool = False):
        self.key = key
        self.reverse = reverse

    def apply(self, data: Any) -> Any:
        if not isinstance(data, list):
            return data

        if self.key:
            return sorted(data, key=lambda x: x.get(self.key, x) if isinstance(x, dict) else x, reverse=self.reverse)
        return sorted(data, reverse=self.reverse)


class LimitFilter(Filter):
    """Фильтр лимита"""

    def __init__(self, limit: int, offset: int = 0):
        self.limit = limit
        self.offset = offset

    def apply(self, data: Any) -> Any:
        if not isinstance(data, list):
            return data
        return data[self.offset:self.offset + self.limit]


class NullFilter(Filter):
    """Фильтр удаления null значений"""

    def __init__(self, keep: bool = False):
        self.keep = keep

    def apply(self, data: Any) -> Any:
        if isinstance(data, list):
            if self.keep:
                return [item for item in data if item is None]
            return [item for item in data if item is not None]
        return data if (data is None) == self.keep else None


# Convenience functions

def by_key(key: str, value: Any) -> KeyFilter:
    """Создание фильтра по ключу"""
    return KeyFilter(key, value)


def by_range(min_val: float = None, max_val: float = None, key: str = None) -> RangeFilter:
    """Создание фильтра по диапазону"""
    return RangeFilter(min_val, max_val, key)


def by_regex(pattern: str, key: str = None) -> RegexFilter:
    """Создание regex фильтра"""
    return RegexFilter(pattern, key)


def by_type(*types: type) -> TypeFilter:
    """Создание типа фильтра"""
    return TypeFilter(*types)


def filter_(func: Callable) -> LambdaFilter:
    """Создание lambda фильтра"""
    return LambdaFilter(func)


def and_(*filters: Filter) -> CompositeFilter:
    """Создание AND фильтра"""
    return CompositeFilter(*filters, mode="and")


def or_(*filters: Filter) -> CompositeFilter:
    """Создание OR фильтра"""
    return CompositeFilter(*filters, mode="or")


def dedupe(key: str = None) -> DedupeFilter:
    """Создание dedupe фильтра"""
    return DedupeFilter(key)


def sort(key: str = None, reverse: bool = False) -> SortFilter:
    """Создание sort фильтра"""
    return SortFilter(key, reverse)


def limit(limit: int, offset: int = 0) -> LimitFilter:
    """Создание limit фильтра"""
    return LimitFilter(limit, offset)


def remove_null(keep: bool = False) -> NullFilter:
    """Создание null фильтра"""
    return NullFilter(keep)
