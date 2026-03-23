"""Iterator utilities"""

from typing import Iterator, List, Callable, Any, TypeVar

T = TypeVar('T')


def iterate(func: Callable, initial: T, condition: Callable[[T], bool]) -> Iterator[T]:
    """Iterate while condition is true"""
    current = initial
    while condition(current):
        yield current
        current = func(current)


def cycle(items: List[T], times: int = None) -> Iterator[T]:
    """Cycle through items"""
    count = 0
    while times is None or count < times:
        for item in items:
            yield item
        count += 1


def take(iterator: Iterator, n: int) -> List[T]:
    """Take first n items"""
    return [next(iterator) for _ in range(n)]


def drop(iterator: Iterator, n: int) -> Iterator:
    """Drop first n items"""
    for _ in range(n):
        next(iterator, None)
    return iterator


def chunk(iterator: Iterator, size: int) -> Iterator[List[T]]:
    """Chunk iterator into lists"""
    chunk = []
    for item in iterator:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
