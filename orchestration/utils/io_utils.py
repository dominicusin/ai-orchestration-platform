"""IO utilities"""

import io
from typing import Any


def string_io(initial: str = "") -> io.StringIO:
    """Create StringIO"""
    return io.StringIO(initial)


def bytes_io(initial: bytes = b"") -> io.BytesIO:
    """Create BytesIO"""
    return io.BytesIO(initial)


def file_io(filename: str, mode: str = "r") -> io.FileIO:
    """Create FileIO"""
    return io.FileIO(filename, mode)


def buffer_read(buffer: io.BytesIO, size: int = -1) -> bytes:
    """Read from buffer"""
    return buffer.read(size)


def buffer_write(buffer: io.BytesIO, data: bytes):
    """Write to buffer"""
    buffer.write(data)
