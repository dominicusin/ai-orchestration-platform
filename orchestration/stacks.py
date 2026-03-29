"""
Stacks - LIFO data structures
Стеки - структуры данных LIFO
"""

from typing import Any


class Stack:
    """Стек"""

    def __init__(self):
        self._items: list = []

    def push(self, item: Any):
        """Добавление элемента"""
        self._items.append(item)

    def pop(self) -> Any:
        """Удаление и возврат верхнего элемента"""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self._items.pop()

    def peek(self) -> Any:
        """Просмотр верхнего элемента без удаления"""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self._items[-1]

    def is_empty(self) -> bool:
        """Проверка пустоты"""
        return len(self._items) == 0

    def size(self) -> int:
        """Размер стека"""
        return len(self._items)

    def clear(self):
        """Очистка стека"""
        self._items.clear()

    def to_list(self) -> list:
        """Преобразование в список"""
        return list(self._items)


class MinStack(Stack):
    """Стек с отслеживанием минимума"""

    def __init__(self):
        super().__init__()
        self._min_items: list = []

    def push(self, item: Any):
        """Добавление с отслеживанием минимума"""
        super().push(item)
        if not self._min_items or item <= self._min_items[-1]:
            self._min_items.append(item)

    def pop(self) -> Any:
        """Удаление с обновлением минимума"""
        item = super().pop()
        if self._min_items and item == self._min_items[-1]:
            self._min_items.pop()
        return item

    def get_min(self) -> Any:
        """Получение минимума"""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self._min_items[-1]


class MaxStack(Stack):
    """Стек с отслеживанием максимума"""

    def __init__(self):
        super().__init__()
        self._max_items: list = []

    def push(self, item: Any):
        """Добавление с отслеживанием максимума"""
        super().push(item)
        if not self._max_items or item >= self._max_items[-1]:
            self._max_items.append(item)

    def pop(self) -> Any:
        """Удаление с обновлением максимума"""
        item = super().pop()
        if self._max_items and item == self._max_items[-1]:
            self._max_items.pop()
        return item

    def get_max(self) -> Any:
        """Получение максимума"""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self._max_items[-1]


class StackWithHistory(Stack):
    """Стек с историей изменений"""

    def __init__(self):
        super().__init__()
        self._history: list = []

    def push(self, item: Any):
        """Добавление с записью в историю"""
        super().push(item)
        self._history.append(("push", item))

    def pop(self) -> Any:
        """Удаление с записью в историю"""
        item = super().pop()
        self._history.append(("pop", item))
        return item

    def get_history(self) -> list:
        """Получение истории"""
        return list(self._history)

    def clear_history(self):
        """Очистка истории"""
        self._history.clear()


# Factory functions

def create_stack() -> Stack:
    """Создание стека"""
    return Stack()


def create_min_stack() -> MinStack:
    """Создание стека с минимумом"""
    return MinStack()


def create_max_stack() -> MaxStack:
    """Создание стека с максимумом"""
    return MaxStack()


def create_stack_with_history() -> StackWithHistory:
    """Создание стека с историей"""
    return StackWithHistory()
