"""Pickle extended utilities"""

import pickle
from typing import Any


def pickle_dumps(obj: Any) -> bytes:
    """Pickle to bytes"""
    return pickle.dumps(obj)


def pickle_loads(data: bytes) -> Any:
    """Unpickle from bytes"""
    return pickle.loads(data)


def pickle_save_zip(obj: Any, path: str):
    """Save pickle with gzip"""
    import gzip
    with gzip.open(path, 'wb') as f:
        pickle.dump(obj, f)


def pickle_load_zip(path: str) -> Any:
    """Load pickle with gzip"""
    import gzip
    with gzip.open(path, 'rb') as f:
        return pickle.load(f)
