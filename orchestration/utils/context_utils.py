"""Context manager utilities"""

import contextlib
from typing import Generator


@contextlib.contextmanager
def timer() -> Generator[dict, None, None]:
    """Time code block"""
    import time
    start = time.perf_counter()
    result = {}
    try:
        yield result
    finally:
        result["elapsed"] = time.perf_counter() - start


@contextlib.contextmanager
def temp_env(**kwargs):
    """Temporarily set environment variables"""
    import os
    old = {}
    for k, v in kwargs.items():
        old[k] = os.environ.get(k)
        os.environ[k] = v
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@contextlib.contextmanager
def temp_dir():
    """Create temporary directory"""
    import tempfile
    import shutil
    path = tempfile.mkdtemp()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
