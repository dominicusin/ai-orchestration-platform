"""
Advanced validators for data validation
Расширенные валидаторы для проверки данных
"""

import re
from typing import Any


class Validator:
    """Базовый валидатор"""

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Валидация. Returns (is_valid, error_message)"""
        raise NotImplementedError


class StringValidator(Validator):
    """Валидатор строки"""

    def __init__(
        self,
        min_length: int = None,
        max_length: int = None,
        pattern: str = None,
        allow_empty: bool = False,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.allow_empty = allow_empty

    def validate(self, value: Any) -> tuple[bool, str | None]:
        if value is None or value == "":
            if self.allow_empty:
                return True, None
            return False, "Value cannot be empty"

        if not isinstance(value, str):
            return False, "Value must be a string"

        if self.min_length and len(value) < self.min_length:
            return False, f"Minimum length is {self.min_length}"

        if self.max_length and len(value) > self.max_length:
            return False, f"Maximum length is {self.max_length}"

        if self.pattern and not self.pattern.match(value):
            return False, "Value does not match required pattern"

        return True, None


class NumberValidator(Validator):
    """Валидатор числа"""

    def __init__(
        self,
        min_value: float = None,
        max_value: float = None,
        integer_only: bool = False,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only

    def validate(self, value: Any) -> tuple[bool, str | None]:
        try:
            num = float(value)
        except (ValueError, TypeError):
            return False, "Value must be a number"

        if self.integer_only and not float(value).is_integer():
            return False, "Value must be an integer"

        if self.min_value is not None and num < self.min_value:
            return False, f"Minimum value is {self.min_value}"

        if self.max_value is not None and num > self.max_value:
            return False, f"Maximum value is {self.max_value}"

        return True, None


class BooleanValidator(Validator):
    """Валидатор булева значения"""

    def validate(self, value: Any) -> tuple[bool, str | None]:
        if isinstance(value, bool):
            return True, None
        if isinstance(value, str) and value.lower() in ("true", "false", "1", "0", "yes", "no"):
            return True, None
        return False, "Value must be a boolean"


class ListValidator(Validator):
    """Валидатор списка"""

    def __init__(
        self,
        min_items: int = None,
        max_items: int = None,
        item_validator: Validator = None,
    ):
        self.min_items = min_items
        self.max_items = max_items
        self.item_validator = item_validator

    def validate(self, value: Any) -> tuple[bool, str | None]:
        if not isinstance(value, list):
            return False, "Value must be a list"

        if self.min_items and len(value) < self.min_items:
            return False, f"Minimum {self.min_items} items required"

        if self.max_items and len(value) > self.max_items:
            return False, f"Maximum {self.max_items} items allowed"

        if self.item_validator:
            for i, item in enumerate(value):
                is_valid, error = self.item_validator.validate(item)
                if not is_valid:
                    return False, f"Item {i}: {error}"

        return True, None


class DictValidator(Validator):
    """Валидатор словаря"""

    def __init__(
        self,
        schema: dict = None,
        required_keys: list = None,
    ):
        self.schema = schema or {}
        self.required_keys = required_keys or []

    def validate(self, value: Any) -> tuple[bool, str | None]:
        if not isinstance(value, dict):
            return False, "Value must be a dictionary"

        for key in self.required_keys:
            if key not in value:
                return False, f"Required key '{key}' is missing"

        for key, validator in self.schema.items():
            if key in value:
                is_valid, error = validator.validate(value[key])
                if not is_valid:
                    return False, f"Key '{key}': {error}"

        return True, None


class EmailValidator(Validator):
    """Валидатор email"""

    PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def validate(self, value: Any) -> tuple[bool, str | None]:
        if not isinstance(value, str):
            return False, "Value must be a string"

        if not self.PATTERN.match(value):
            return False, "Invalid email format"

        return True, None


class URLValidator(Validator):
    """Валидатор URL"""

    PATTERN = re.compile(r"^https?://")

    def validate(self, value: Any) -> tuple[bool, str | None]:
        if not isinstance(value, str):
            return False, "Value must be a string"

        if not self.PATTERN.match(value):
            return False, "Invalid URL format (must start with http:// or https://)"

        return True, None


class ChoiceValidator(Validator):
    """Валидатор выбора из списка"""

    def __init__(self, choices: list, case_sensitive: bool = True):
        self.choices = choices
        self.case_sensitive = case_sensitive

    def validate(self, value: Any) -> tuple[bool, str | None]:
        if not self.case_sensitive and isinstance(value, str):
            value = value.lower()
            choices = [c.lower() if isinstance(c, str) else c for c in self.choices]
        else:
            choices = self.choices

        if value not in choices:
            return False, f"Value must be one of: {self.choices}"

        return True, None


class CompositeValidator(Validator):
    """Композитный валидатор"""

    def __init__(self, *validators: Validator, mode: str = "all"):
        self.validators = validators
        self.mode = mode

    def validate(self, value: Any) -> tuple[bool, str | None]:
        if self.mode == "all":
            for v in self.validators:
                is_valid, error = v.validate(value)
                if not is_valid:
                    return False, error
            return True, None
        else:
            for v in self.validators:
                is_valid, error = v.validate(value)
                if is_valid:
                    return True, None
            return False, "None of the validators passed"


class OptionalValidator(Validator):
    """Опциональный валидатор"""

    def __init__(self, validator: Validator, allow_none: bool = True):
        self.validator = validator
        self.allow_none = allow_none

    def validate(self, value: Any) -> tuple[bool, str | None]:
        if value is None:
            if self.allow_none:
                return True, None
            return False, "Value cannot be None"

        return self.validator.validate(value)


def validate(value: Any, validator: Validator) -> bool:
    """Упрощённая валидация"""
    is_valid, _ = validator.validate(value)
    return is_valid


def validate_or_raise(value: Any, validator: Validator, error_class: type = ValueError):
    """Валидация с выбросом исключения"""
    is_valid, error = validator.validate(value)
    if not is_valid:
        raise error_class(error)
    return value
