"""
Configuration validator
Валидатор конфигурации
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ValidationError(Exception):
    """Ошибка валидации"""
    pass


@dataclass
class ValidationResult:
    """Результат валидации"""
    valid: bool
    errors: list[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        self.errors = self.errors or []
        self.warnings = self.warnings or []


class ConfigValidator:
    """
    Валидатор конфигурации
    """

    def __init__(self):
        self.rules = {}

    def add_rule(self, name: str, validator: callable, error_msg: str):
        """Добавление правила валидации"""
        self.rules[name] = {"validator": validator, "error": error_msg}

    def validate(self, config: dict) -> ValidationResult:
        """Валидация конфигурации"""
        errors = []
        warnings = []

        for name, rule in self.rules.items():
            try:
                if not rule["validator"](config):
                    errors.append(rule["error"])
            except Exception as e:
                errors.append(f"Rule {name} failed: {e}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


# Standard validators

def validate_port(value: Any) -> bool:
    """Валидация порта"""
    if isinstance(value, int):
        return 1 <= value <= 65535
    if isinstance(value, str):
        return value.isdigit() and 1 <= int(value) <= 65535
    return False


def validate_url(value: Any) -> bool:
    """Валидация URL"""
    if not isinstance(value, str):
        return False
    pattern = r"^https?://"
    return bool(re.match(pattern, value))


def validate_path(value: Any) -> bool:
    """Валидация пути"""
    if isinstance(value, str):
        try:
            Path(value)
            return True
        except Exception:
            return False
    return False


def validate_positive_int(value: Any) -> bool:
    """Валидация положительного целого"""
    if isinstance(value, int):
        return value > 0
    if isinstance(value, str):
        return value.isdigit() and int(value) > 0
    return False


def validate_range(value: Any, min_val: int, max_val: int) -> bool:
    """Валидация диапазона"""
    try:
        val = int(value) if isinstance(value, str) else value
        return min_val <= val <= max_val
    except (ValueError, TypeError):
        return False


def validate_env_var(value: Any) -> bool:
    """Валидация имени переменной окружения"""
    if not isinstance(value, str):
        return False
    return bool(re.match(r"^[A-Z][A-Z0-9_]*$", value))


def validate_json_string(value: Any) -> bool:
    """Валидация JSON строки"""
    if not isinstance(value, str):
        return False
    import json
    try:
        json.loads(value)
        return True
    except json.JSONDecodeError:
        return False


# Default validation rules for AI Pipeline

def create_pipeline_validator() -> ConfigValidator:
    """Создание валидатора для pipeline"""
    validator = ConfigValidator()

    # Required fields
    validator.add_rule(
        "project_path",
        lambda c: "project_path" in c and c["project_path"],
        "project_path is required",
    )

    validator.add_rule(
        "output_path",
        lambda c: "output_path" in c and c["output_path"],
        "output_path is required",
    )

    # Port validation
    validator.add_rule(
        "prometheus_port",
        lambda c: "prometheus_port" not in c or validate_port(c["prometheus_port"]),
        "prometheus_port must be between 1 and 65535",
    )

    # Positive integers
    validator.add_rule(
        "max_workers",
        lambda c: "max_workers" not in c or validate_positive_int(c["max_workers"]),
        "max_workers must be a positive integer",
    )

    # URLs
    validator.add_rule(
        "ollama_url",
        lambda c: "ollama_url" not in c or validate_url(c["ollama_url"]),
        "ollama_url must be a valid URL",
    )

    # Environment variables
    validator.add_rule(
        "valid_env_vars",
        lambda c: all(validate_env_var(v) for v in c.get("env_vars", {}).keys()),
        "Environment variable names must be uppercase with underscores",
    )

    return validator


# Quick validation function

def validate_pipeline_config(config: dict) -> ValidationResult:
    """Быстрая валидация конфигурации pipeline"""
    validator = create_pipeline_validator()
    return validator.validate(config)


# Schema validation

PIPELINE_SCHEMA = {
    "type": "object",
    "required": ["project_path", "output_path"],
    "properties": {
        "project_path": {"type": "string"},
        "output_path": {"type": "string"},
        "max_workers": {"type": "integer", "minimum": 1, "maximum": 100},
        "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
        "log_format": {"type": "string", "enum": ["json", "text"]},
        "cache_policy": {"type": "string", "enum": ["cache_first", "ai_first", "skip_cache"]},
        "default_provider": {"type": "string"},
        "ollama_url": {"type": "string", "format": "uri"},
        "prometheus_port": {"type": "integer", "minimum": 1, "maximum": 65535},
    },
}


def validate_against_schema(config: dict, schema: dict = None) -> ValidationResult:
    """Валидация по схеме"""
    schema = schema or PIPELINE_SCHEMA
    errors = []
    warnings = []

    # Check required fields
    for field in schema.get("required", []):
        if field not in config:
            errors.append(f"Missing required field: {field}")

    # Check types and values
    for field, spec in schema.get("properties", {}).items():
        if field not in config:
            continue

        value = config[field]
        field_type = spec.get("type")

        # Type checking
        if field_type == "string" and not isinstance(value, str):
            errors.append(f"{field} must be a string")
        elif field_type == "integer" and not isinstance(value, int):
            errors.append(f"{field} must be an integer")

        # Enum checking
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"{field} must be one of: {spec['enum']}")

        # Range checking
        if field_type == "integer":
            if "minimum" in spec and value < spec["minimum"]:
                errors.append(f"{field} must be >= {spec['minimum']}")
            if "maximum" in spec and value > spec["maximum"]:
                errors.append(f"{field} must be <= {spec['maximum']}")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
