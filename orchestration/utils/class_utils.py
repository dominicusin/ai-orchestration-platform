"""Class utilities"""

from typing import Any, Dict


def get_attrs(obj: object) -> Dict[str, Any]:
    """Get object attributes"""
    return {k: getattr(obj, k) for k in dir(obj) if not k.startswith('_')}


def set_attrs(obj: object, **kwargs):
    """Set object attributes"""
    for k, v in kwargs.items():
        setattr(obj, k, v)


def has_method(obj: object, name: str) -> bool:
    """Check if object has method"""
    return hasattr(obj, name) and callable(getattr(obj, name))


def get_methods(obj: object) -> list:
    """Get object methods"""
    return [m for m in dir(obj) if callable(getattr(obj, m)) and not m.startswith('_')]


def copy_attrs(src: object, dst: object, exclude: list = None):
    """Copy attributes from one object to another"""
    exclude = exclude or []
    for k in dir(src):
        if k not in exclude and not k.startswith('_'):
            if hasattr(dst, k):
                setattr(dst, k, getattr(src, k))
