"""Iterator utilities"""

from collections.abc import Callable, Iterator
from typing import TypeVar

T = TypeVar('T')


def iterate(func: Callable, initial: T, condition: Callable[[T], bool]) -> Iterator[T]:
    """Iterate while condition is true"""
    current = initial
    while condition(current):
        yield current
        current = func(current)


def cycle(items: list[T], times: int = None) -> Iterator[T]:
    """Cycle through items"""
    count = 0
    while times is None or count < times:
        yield from items
        count += 1


def take(iterator: Iterator, n: int) -> list[T]:
    """Take first n items"""
    return [next(iterator) for _ in range(n)]


def drop(iterator: Iterator, n: int) -> Iterator:
    """Drop first n items"""
    for _ in range(n):
        next(iterator, None)
    return iterator


def chunk(iterator: Iterator, size: int) -> Iterator[list[T]]:
    """Chunk iterator into lists"""
    chunk = []
    for item in iterator:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
