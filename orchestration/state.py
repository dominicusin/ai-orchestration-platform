"""
State management
Управление состоянием
"""

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StateStatus(Enum):
    """Статус состояния"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class StateTransition:
    """Переход состояния"""
    from_state: StateStatus
    to_state: StateStatus
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


@dataclass
class State:
    """Состояние"""
    name: str
    status: StateStatus = StateStatus.PENDING
    data: Any = None
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    transitions: list[StateTransition] = field(default_factory=list)

    def update(self, status: StateStatus, data: Any = None, metadata: dict = None):
        """Обновление состояния"""
        transition = StateTransition(
            from_state=self.status,
            to_state=status,
        )
        self.transitions.append(transition)

        self.status = status
        self.updated_at = time.time()

        if data is not None:
            self.data = data

        if metadata:
            self.metadata.update(metadata)

    def is_active(self) -> bool:
        """Активно?"""
        return self.status == StateStatus.ACTIVE

    def is_completed(self) -> bool:
        """Завершено?"""
        return self.status == StateStatus.COMPLETED

    def is_failed(self) -> bool:
        """Ошибка?"""
        return self.status == StateStatus.FAILED

    def to_dict(self) -> dict:
        """Сериализация"""
        return {
            "name": self.name,
            "status": self.status.value,
            "data": str(self.data),
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "transitions_count": len(self.transitions),
        }


class StateMachine:
    """Машина состояний"""

    def __init__(self, name: str = "default"):
        self.name = name
        self._states: dict[str, State] = {}
        self._transitions: dict[StateStatus, list[StateStatus]] = defaultdict(list)
        self._on_enter: dict[StateStatus, list[Callable]] = defaultdict(list)
        self._on_exit: dict[StateStatus, list[Callable]] = defaultdict(list)

    def add_state(self, name: str, status: StateStatus = StateStatus.PENDING) -> State:
        """Добавление состояния"""
        state = State(name=name, status=status)
        self._states[name] = state
        return state

    def add_transition(self, from_state: StateStatus, to_state: StateStatus):
        """Добавление допустимого перехода"""
        self._transitions[from_state].append(to_state)

    def can_transition(self, state_name: str, to_status: StateStatus) -> bool:
        """Проверка допустимости перехода"""
        state = self._states.get(state_name)
        if not state:
            return False

        allowed = self._transitions.get(state.status, [])
        return to_status in allowed

    def transition(self, state_name: str, to_status: StateStatus, data: Any = None, metadata: dict = None) -> bool:
        """Выполнение перехода"""
        state = self._states.get(state_name)
        if not state:
            return False

        if not self.can_transition(state_name, to_status):
            return False

        # Call exit callback
        for callback in self._on_exit.get(state.status, []):
            callback(state)

        state.update(to_status, data, metadata)

        # Call enter callback
        for callback in self._on_enter.get(to_status, []):
            callback(state)

        return True

    def get_state(self, name: str) -> State | None:
        """Получение состояния"""
        return self._states.get(name)

    def get_states_by_status(self, status: StateStatus) -> list[State]:
        """Получение состояний по статусу"""
        return [s for s in self._states.values() if s.status == status]

    def on_enter(self, status: StateStatus, callback: Callable):
        """Обработчик входа в состояние"""
        self._on_enter[status].append(callback)

    def on_exit(self, status: StateStatus, callback: Callable):
        """Обработчик выхода из состояния"""
        self._on_exit[status].append(callback)

    def list_states(self) -> list[str]:
        """Список состояний"""
        return list(self._states.keys())


class StateStore:
    """Хранилище состояний"""

    def __init__(self):
        self._states: dict[str, State] = {}
        self._history: dict[str, list[State]] = defaultdict(list)
        self._max_history: int = 100

    def save(self, state: State):
        """Сохранение состояния"""
        # Save to history
        if state.name in self._states:
            self._history[state.name].append(self._states[state.name])
            if len(self._history[state.name]) > self._max_history:
                self._history[state.name].pop(0)

        self._states[state.name] = state

    def load(self, name: str) -> State | None:
        """Загрузка состояния"""
        return self._states.get(name)

    def delete(self, name: str) -> bool:
        """Удаление состояния"""
        if name in self._states:
            del self._states[name]
            return True
        return False

    def list_names(self) -> list[str]:
        """Список имён состояний"""
        return list(self._states.keys())

    def get_history(self, name: str) -> list[State]:
        """История состояния"""
        return self._history.get(name, [])

    def clear(self):
        """Очистка"""
        self._states.clear()
        self._history.clear()


class StateManager:
    """Менеджер состояний"""

    def __init__(self):
        self._machines: dict[str, StateMachine] = {}
        self._stores: dict[str, StateStore] = {}

    def create_machine(self, name: str) -> StateMachine:
        """Создание машины состояний"""
        machine = StateMachine(name)
        self._machines[name] = machine
        return machine

    def get_machine(self, name: str) -> StateMachine | None:
        """Получение машины"""
        return self._machines.get(name)

    def create_store(self, name: str = "default") -> StateStore:
        """Создание хранилища"""
        store = StateStore()
        self._stores[name] = store
        return store

    def get_store(self, name: str = "default") -> StateStore | None:
        """Получение хранилища"""
        return self._stores.get(name)


# Singleton
_manager: StateManager | None = None


def get_state_manager() -> StateManager:
    """Получение менеджера состояний"""
    global _manager
    if _manager is None:
        _manager = StateManager()
    return _manager
