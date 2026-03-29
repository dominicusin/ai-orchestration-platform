"""
Results handling
Обработка результатов операций
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ResultStatus(Enum):
    """Статус результата"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class Result:
    """Результат операции"""
    status: ResultStatus
    data: Any = None
    error: str = None
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    def is_success(self) -> bool:
        """Успешный результат?"""
        return self.status == ResultStatus.SUCCESS

    def is_failure(self) -> bool:
        """Неудачный результат?"""
        return self.status == ResultStatus.FAILURE

    def is_pending(self) -> bool:
        """Ожидающий результат?"""
        return self.status == ResultStatus.PENDING

    def get_data(self, default: Any = None) -> Any:
        """Получение данных с默认值"""
        return self.data if self.data is not None else default


class ResultBuilder:
    """Строитель результатов"""

    def __init__(self):
        self._status = ResultStatus.PENDING
        self._data = None
        self._error = None
        self._message = ""
        self._metadata = {}

    def success(self, data: Any = None, message: str = "") -> Result:
        """Успешный результат"""
        return Result(
            status=ResultStatus.SUCCESS,
            data=data,
            message=message,
            metadata=self._metadata,
        )

    def failure(self, error: str, message: str = "") -> Result:
        """Неудачный результат"""
        return Result(
            status=ResultStatus.FAILURE,
            error=error,
            message=message,
            metadata=self._metadata,
        )

    def partial(self, data: Any = None, message: str = "") -> Result:
        """Частичный результат"""
        return Result(
            status=ResultStatus.PARTIAL,
            data=data,
            message=message,
            metadata=self._metadata,
        )

    def pending(self, message: str = "") -> Result:
        """Ожидающий результат"""
        return Result(
            status=ResultStatus.PENDING,
            message=message,
            metadata=self._metadata,
        )

    def cancelled(self, message: str = "") -> Result:
        """Отменённый результат"""
        return Result(
            status=ResultStatus.CANCELLED,
            message=message,
            metadata=self._metadata,
        )

    def with_metadata(self, key: str, value: Any) -> "ResultBuilder":
        """Добавление метаданных"""
        self._metadata[key] = value
        return self


def success(data: Any = None, message: str = "") -> Result:
    """Создание успешного результата"""
    return Result(
        status=ResultStatus.SUCCESS,
        data=data,
        message=message,
    )


def failure(error: str, message: str = "") -> Result:
    """Создание неудачного результата"""
    return Result(
        status=ResultStatus.FAILURE,
        error=error,
        message=message,
    )


def partial(data: Any = None, message: str = "") -> Result:
    """Создание частичного результата"""
    return Result(
        status=ResultStatus.PARTIAL,
        data=data,
        message=message,
    )


class ResultCollection:
    """Коллекция результатов"""

    def __init__(self):
        self._results: list[Result] = []

    def add(self, result: Result):
        """Добавление результата"""
        self._results.append(result)

    def get_all(self) -> list[Result]:
        """Получение всех результатов"""
        return list(self._results)

    def get_successful(self) -> list[Result]:
        """Получение успешных результатов"""
        return [r for r in self._results if r.is_success()]

    def get_failed(self) -> list[Result]:
        """Получение неудачных результатов"""
        return [r for r in self._results if r.is_failure()]

    def is_all_success(self) -> bool:
        """Все успешны?"""
        return all(r.is_success() for r in self._results)

    def is_any_failure(self) -> bool:
        """Есть неудачи?"""
        return any(r.is_failure() for r in self._results)

    def count(self) -> int:
        """Количество"""
        return len(self._results)

    def successful_count(self) -> int:
        """Количество успешных"""
        return len(self.get_successful())

    def failed_count(self) -> int:
        """Количество неудачных"""
        return len(self.get_failed())
