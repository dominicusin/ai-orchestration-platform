"""
Input validators
Валидаторы входных данных
"""

import re
from collections.abc import Callable
from typing import Any


class Validator:
    """Базовый класс валидатора"""

    def validate(self, value: Any) -> bool:
        """Валидация значения"""
        raise NotImplementedError

    def get_error(self) -> str:
        """Получение сообщения об ошибке"""
        raise NotImplementedError


class RequiredValidator(Validator):
    """Валидатор обязательного поля"""

    def __init__(self, message: str = "This field is required"):
        self.message = message

    def validate(self, value: Any) -> bool:
        return value is not None and value != ""

    def get_error(self) -> str:
        return self.message


class TypeValidator(Validator):
    """Валидатор типа"""

    def __init__(self, expected_type: type, message: str = None):
        self.expected_type = expected_type
        self.message = message or f"Expected {expected_type.__name__}"

    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        return isinstance(value, self.expected_type)

    def get_error(self) -> str:
        return self.message


class RangeValidator(Validator):
    """Валидатор диапазона"""

    def __init__(self, min_val: float = None, max_val: float = None):
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        try:
            val = float(value)
            if self.min_val is not None and val < self.min_val:
                return False
            if self.max_val is not None and val > self.max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False

    def get_error(self) -> str:
        if self.min_val is not None and self.max_val is not None:
            return f"Value must be between {self.min_val} and {self.max_val}"
        elif self.min_val is not None:
            return f"Value must be at least {self.min_val}"
        elif self.max_val is not None:
            return f"Value must be at most {self.max_val}"
        return "Invalid value"


class LengthValidator(Validator):
    """Валидатор длины"""

    def __init__(self, min_len: int = None, max_len: int = None):
        self.min_len = min_len
        self.max_len = max_len

    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        try:
            length = len(value)
            if self.min_len is not None and length < self.min_len:
                return False
            if self.max_len is not None and length > self.max_len:
                return False
            return True
        except TypeError:
            return False

    def get_error(self) -> str:
        if self.min_len is not None and self.max_len is not None:
            return f"Length must be between {self.min_len} and {self.max_len}"
        elif self.min_len is not None:
            return f"Length must be at least {self.min_len}"
        elif self.max_len is not None:
            return f"Length must be at most {self.max_len}"
        return "Invalid length"


class PatternValidator(Validator):
    """Валидатор по регулярному выражению"""

    def __init__(self, pattern: str, message: str = "Invalid format"):
        self.pattern = re.compile(pattern)
        self.message = message

    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        return bool(self.pattern.match(str(value)))

    def get_error(self) -> str:
        return self.message


class EmailValidator(PatternValidator):
    """Валидатор email"""

    def __init__(self):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        super().__init__(pattern, "Invalid email address")


class URLValidator(PatternValidator):
    """Валидатор URL"""

    def __init__(self):
        pattern = r"^https?://"
        super().__init__(pattern, "Invalid URL")


class CustomValidator(Validator):
    """Кастомный валидатор"""

    def __init__(self, func: Callable[[Any], bool], message: str = "Invalid value"):
        self.func = func
        self.message = message

    def validate(self, value: Any) -> bool:
        try:
            return self.func(value)
        except Exception:
            return False

    def get_error(self) -> str:
        return self.message


class AndValidator(Validator):
    """Объединение валидаторов (AND)"""

    def __init__(self, *validators: Validator):
        self.validators = validators
        self._errors = []

    def validate(self, value: Any) -> bool:
        self._errors = []
        for validator in self.validators:
            if not validator.validate(value):
                self._errors.append(validator.get_error())
        return len(self._errors) == 0

    def get_error(self) -> str:
        return "; ".join(self._errors) if self._errors else "Invalid value"


class OrValidator(Validator):
    """Объединение валидаторов (OR) - достаточно одного"""

    def __init__(self, *validators: Validator):
        self.validators = validators

    def validate(self, value: Any) -> bool:
        for validator in self.validators:
            if validator.validate(value):
                return True
        return False

    def get_error(self) -> str:
        return "None of the validators passed"


class SchemaValidator(Validator):
    """Валидатор по схеме"""

    def __init__(self, schema: dict):
        self.schema = schema
        self._errors = []

    def validate(self, value: Any) -> bool:
        self._errors = []

        if not isinstance(value, dict):
            self._errors.append("Expected object")
            return False

        for field, validators in self.schema.items():
            field_value = value.get(field)

            if isinstance(validators, list):
                for v in validators:
                    if not v.validate(field_value):
                        self._errors.append(f"{field}: {v.get_error()}")
            else:
                if not validators.validate(field_value):
                    self._errors.append(f"{field}: {validators.get_error()}")

        return len(self._errors) == 0

    def get_error(self) -> str:
        return "; ".join(self._errors)


# Convenience functions

def required(message: str = None) -> RequiredValidator:
    """Создание required валидатора"""
    return RequiredValidator(message)


def is_type(expected_type: type, message: str = None) -> TypeValidator:
    """Создание type валидатора"""
    return TypeValidator(expected_type, message)


def range(min_val: float = None, max_val: float = None) -> RangeValidator:
    """Создание range валидатора"""
    return RangeValidator(min_val, max_val)


def length(min_len: int = None, max_len: int = None) -> LengthValidator:
    """Создание length валидатора"""
    return LengthValidator(min_len, max_len)


def pattern(pattern: str, message: str = None) -> PatternValidator:
    """Создание pattern валидатора"""
    return PatternValidator(pattern, message)


def email() -> EmailValidator:
    """Создание email валидатора"""
    return EmailValidator()


def url() -> URLValidator:
    """Создание URL валидатора"""
    return URLValidator()


def custom(func: Callable, message: str = None) -> CustomValidator:
    """Создание custom валидатора"""
    return CustomValidator(func, message)


def and_(*validators: Validator) -> AndValidator:
    """Создание AND валидатора"""
    return AndValidator(*validators)


def or_(*validators: OrValidator) -> OrValidator:
    """Создание OR валидатора"""
    return OrValidator(*validators)


def schema(schema: dict) -> SchemaValidator:
    """Создание schema валидатора"""
    return SchemaValidator(schema)
