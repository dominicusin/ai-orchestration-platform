"""
Data transformers
Трансформеры данных
"""

import re
from collections.abc import Callable
from typing import Any


class Transformer:
    """Базовый трансформер"""

    def transform(self, data: Any) -> Any:
        """Трансформация данных"""
        raise NotImplementedError


class MapTransformer(Transformer):
    """Трансформер применяющий функцию к каждому элементу"""

    def __init__(self, func: Callable):
        self.func = func

    def transform(self, data: Any) -> Any:
        if isinstance(data, list):
            return [self.func(item) for item in data]
        return self.func(data)


class FilterTransformer(Transformer):
    """Трансформер фильтрации"""

    def __init__(self, predicate: Callable):
        self.predicate = predicate

    def transform(self, data: Any) -> Any:
        if isinstance(data, list):
            return [item for item in data if self.predicate(item)]
        return data


class FlatMapTransformer(Transformer):
    """Трансформер для flatten и map"""

    def __init__(self, func: Callable):
        self.func = func

    def transform(self, data: Any) -> Any:
        if isinstance(data, list):
            result = []
            for item in data:
                transformed = self.func(item)
                if isinstance(transformed, list):
                    result.extend(transformed)
                else:
                    result.append(transformed)
            return result
        return self.func(data)


class RenameKeysTransformer(Transformer):
    """Трансформер переименования ключей"""

    def __init__(self, mapping: dict):
        self.mapping = mapping

    def transform(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {self.mapping.get(k, k): v for k, v in data.items()}
        return data


class SelectKeysTransformer(Transformer):
    """Трансформер выбора ключей"""

    def __init__(self, keys: list):
        self.keys = set(keys)

    def transform(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k in self.keys}
        return data


class ExcludeKeysTransformer(Transformer):
    """Трансформер исключения ключей"""

    def __init__(self, keys: list):
        self.keys = set(keys)

    def transform(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k not in self.keys}
        return data


class MergeTransformer(Transformer):
    """Трансформер объединения словарей"""

    def __init__(self, *others: dict):
        self.others = others

    def transform(self, data: Any) -> Any:
        if isinstance(data, dict):
            result = dict(data)
            for other in self.others:
                if isinstance(other, dict):
                    result.update(other)
            return result
        return data


class DefaultValueTransformer(Transformer):
    """Трансформер установки значений по умолчанию"""

    def __init__(self, defaults: dict):
        self.defaults = defaults

    def transform(self, data: Any) -> Any:
        if isinstance(data, dict):
            result = dict(self.defaults)
            result.update(data)
            return result
        return data


class RegexReplaceTransformer(Transformer):
    """Трансформер regex замены"""

    def __init__(self, pattern: str, replacement: str):
        self.pattern = re.compile(pattern)
        self.replacement = replacement

    def transform(self, data: Any) -> Any:
        if isinstance(data, str):
            return self.pattern.sub(self.replacement, data)
        if isinstance(data, dict):
            return {k: self.transform(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self.transform(item) for item in data]
        return data


class ChainTransformer(Transformer):
    """Цепочка трансформеров"""

    def __init__(self, *transformers: Transformer):
        self.transformers = transformers

    def transform(self, data: Any) -> Any:
        result = data
        for t in self.transformers:
            result = t.transform(result)
        return result

    def add(self, transformer: Transformer):
        """Добавление трансформера в цепочку"""
        self.transformers = (*self.transformers, transformer)


# Pipeline функции

def transform(data: Any, *transformers: Transformer) -> Any:
    """Применение цепочки трансформеров"""
    chain = ChainTransformer(*transformers)
    return chain.transform(data)


def map_(func: Callable) -> MapTransformer:
    """Создание map трансформера"""
    return MapTransformer(func)


def filter_(predicate: Callable) -> FilterTransformer:
    """Создание filter трансформера"""
    return FilterTransformer(predicate)


def flat_map(func: Callable) -> FlatMapTransformer:
    """Создание flat_map трансформера"""
    return FlatMapTransformer(func)


def rename_keys(mapping: dict) -> RenameKeysTransformer:
    """Создание rename_keys трансформера"""
    return RenameKeysTransformer(mapping)


def select_keys(keys: list) -> SelectKeysTransformer:
    """Создание select_keys трансформера"""
    return SelectKeysTransformer(keys)


def exclude_keys(keys: list) -> ExcludeKeysTransformer:
    """Создание exclude_keys трансформера"""
    return ExcludeKeysTransformer(keys)


def merge(*others: dict) -> MergeTransformer:
    """Создание merge трансформера"""
    return MergeTransformer(*others)


def defaults(defaults: dict) -> DefaultValueTransformer:
    """Создание defaults трансформера"""
    return DefaultValueTransformer(defaults)


def regex_replace(pattern: str, replacement: str) -> RegexReplaceTransformer:
    """Создание regex_replace трансформера"""
    return RegexReplaceTransformer(pattern, replacement)
