"""
Data class utilities
Утилиты для работы с dataclasses
"""

import json
from dataclasses import asdict, field, fields, is_dataclass
from typing import Any, get_type_hints


def dataclass_to_dict(obj: Any) -> dict:
    """Конвертация dataclass в dict"""
    if is_dataclass(obj):
        return asdict(obj)
    return {}


def dict_to_dataclass(cls: type, data: dict) -> Any:
    """Конвертация dict в dataclass"""
    if not is_dataclass(cls):
        raise ValueError(f"{cls} is not a dataclass")

    # Filter to only known fields
    field_names = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in data.items() if k in field_names}

    return cls(**filtered)


def merge_dataclasses(base: Any, override: dict) -> Any:
    """Объединение dataclass с dict"""
    if not is_dataclass(base):
        raise ValueError("base must be a dataclass")

    base_dict = dataclass_to_dict(base)
    base_dict.update(override)

    return type(base)(**base_dict)


def validate_dataclass(obj: Any) -> list[str]:
    """Валидация dataclass"""
    if not is_dataclass(obj):
        return ["Object is not a dataclass"]

    errors = []
    hints = get_type_hints(type(obj))

    for f in fields(obj):
        value = getattr(obj, f.name)

        # Check required
        if value is None and f.default is field.default and f.default_factory is field(default_factory=lambda: None):
            errors.append(f"Missing required field: {f.name}")

        # Check type
        if value is not None and f.name in hints:
            expected = hints[f.name]
            if not isinstance(value, expected):
                errors.append(f"Field {f.name} type mismatch: expected {expected}, got {type(value)}")

    return errors


def dataclass_to_json(obj: Any, indent: int = 2) -> str:
    """Сериализация dataclass в JSON"""
    return json.dumps(dataclass_to_dict(obj), indent=indent, default=str)


def dataclass_from_json(cls: type, json_str: str) -> Any:
    """Десериализация JSON в dataclass"""
    data = json.loads(json_str)
    return dict_to_dataclass(cls, data)


def clone_dataclass(obj: Any) -> Any:
    """Клонирование dataclass"""
    if not is_dataclass(obj):
        raise ValueError("Object is not a dataclass")

    return type(obj)(**dataclass_to_dict(obj))


def compare_dataclasses(a: Any, b: Any) -> dict[str, Any]:
    """Сравнение двух dataclasses"""
    if not is_dataclass(a) or not is_dataclass(b):
        raise ValueError("Both objects must be dataclasses")

    if not isinstance(a, type(b)):
        return {"error": "Different types"}

    diff = {}
    a_dict = dataclass_to_dict(a)
    b_dict = dataclass_to_dict(b)

    for key in a_dict:
        if a_dict[key] != b_dict.get(key):
            diff[key] = {"old": a_dict[key], "new": b_dict.get(key)}

    return diff
