"""Benchmarking utilities"""

import functools
import time
from collections.abc import Callable


class Timer:
    """Simple timer"""

    def __init__(self):
        self.start = time.time()
        self.end = None

    def stop(self) -> float:
        self.end = time.time()
        return self.elapsed()

    def elapsed(self) -> float:
        end = self.end or time.time()
        return end - self.start


def benchmark(func: Callable) -> Callable:
    """Benchmark decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.4f}s")
        return result
    return wrapper


def measure(iterations: int = 1000):
    """Measure decorator"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            for _ in range(iterations):
                func(*args, **kwargs)
            end = time.perf_counter()
            avg = (end - start) / iterations
            print(f"{func.__name__}: {avg*1000:.4f}ms avg over {iterations} runs")
            return func(*args, **kwargs)
        return wrapper
    return decorator
