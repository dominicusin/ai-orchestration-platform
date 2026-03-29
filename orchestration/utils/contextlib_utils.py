"""Contextlib utilities"""

import contextlib
from collections.abc import Generator
from typing import Any


@contextlib.contextmanager
def nested(*contexts) -> Generator:
    """Nested context managers"""
    with contextlib.nested(*contexts):
        yield


@contextlib.contextmanager
def closing(thing: Any):
    """Auto-close context"""
    try:
        yield thing
    finally:
        thing.close()


@contextlib.contextmanager
def suppress(*exceptions):
    """Suppress exceptions"""
    with contextlib.suppress(*exceptions):
        yield


def contextmanager(func):
    """Context manager decorator"""
    return contextlib.contextmanager(func)
