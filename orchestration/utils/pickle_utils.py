"""Pickle utilities"""

import pickle
from typing import Any


def pickle_load(data: bytes) -> Any:
    """Load from pickle bytes"""
    return pickle.loads(data)


def pickle_dump(obj: Any) -> bytes:
    """Dump to pickle bytes"""
    return pickle.dumps(obj)


def pickle_save(obj: Any, path: str):
    """Save object to file"""
    with open(path, 'wb') as f:
        pickle.dump(obj, f)


def pickle_load_file(path: str) -> Any:
    """Load object from file"""
    with open(path, 'rb') as f:
        return pickle.load(f)
