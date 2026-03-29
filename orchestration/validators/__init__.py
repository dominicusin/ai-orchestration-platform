"""Validators module"""

from typing import Any


class BaseValidator:
    def validate(self, value: Any) -> bool:
        raise NotImplementedError


class StringValidator(BaseValidator):
    def validate(self, value: Any) -> bool:
        return isinstance(value, str)


def get_validators():
    return {"string": StringValidator()}
