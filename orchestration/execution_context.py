"""
Execution context
Контекст выполнения
"""

import contextvars
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Context variable for storing current execution context
_current_context: contextvars.ContextVar["ExecutionContext"] = contextvars.ContextVar(
    "execution_context"
)


@dataclass
class ExecutionContext:
    """Контекст выполнения"""
    request_id: str = ""
    user_id: str = ""
    session_id: str = ""
    metadata: dict = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения"""
        return self.metadata.get(key, default)

    def set(self, key: str, value: Any):
        """Установка значения"""
        self.metadata[key] = value

    def add_tag(self, tag: str):
        """Добавление тега"""
        if tag not in self.tags:
            self.tags.append(tag)

    def duration(self) -> float:
        """Длительность в секундах"""
        return (datetime.now() - self.started_at).total_seconds()


class ContextManager:
    """Менеджер контекста"""

    def __init__(self):
        pass

    def get_context(self) -> ExecutionContext:
        """Получение текущего контекста"""
        ctx = _current_context.get()
        if ctx is None:
            ctx = ExecutionContext()
            _current_context.set(ctx)
        return ctx

    def set_context(self, context: ExecutionContext):
        """Установка контекста"""
        _current_context.set(context)

    def clear(self):
        """Очистка контекста"""
        _current_context.set(ExecutionContext())

    def create_child(self, **kwargs) -> ExecutionContext:
        """Создание дочернего контекста"""
        parent = self.get_context()
        child = ExecutionContext(
            request_id=kwargs.get("request_id", parent.request_id),
            user_id=kwargs.get("user_id", parent.user_id),
            session_id=kwargs.get("session_id", parent.session_id),
            metadata={**parent.metadata, **kwargs.get("metadata", {})},
            tags=list(parent.tags),
        )
        _current_context.set(child)
        return child


# Convenience functions

def get_request_id() -> str:
    """Получение ID запроса"""
    return ContextManager().get_context().request_id


def set_request_id(request_id: str):
    """Установка ID запроса"""
    ContextManager().get_context().request_id = request_id


def get_user_id() -> str:
    """Получение ID пользователя"""
    return ContextManager().get_context().user_id


def set_user_id(user_id: str):
    """Установка ID пользователя"""
    ContextManager().get_context().user_id = user_id


def get_context_value(key: str, default: Any = None) -> Any:
    """Получение значения из контекста"""
    return ContextManager().get_context().get(key, default)


def set_context_value(key: str, value: Any):
    """Установка значения в контекст"""
    ContextManager().get_context().set(key, value)


def add_context_tag(tag: str):
    """Добавление тега"""
    ContextManager().get_context().add_tag(tag)


# Context manager for easy use

def context(**kwargs) -> ExecutionContext:
    """Контекстный менеджер"""
    return ContextManager().create_child(**kwargs)
