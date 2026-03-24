"""ABC utilities"""

import abc
from typing import Type


def abstract_class(cls: Type):
    """Mark class as abstract"""
    return abc.abstractmethod(cls)


def abstract_method(func):
    """Mark method as abstract"""
    return abc.abstractmethod(func)


def abstract_property(func):
    """Mark property as abstract"""
    return property(abc.abstractmethod(func))


def register_subclass(cls: Type, subclass: Type):
    """Register subclass for abstract class"""
    cls.register(subclass)
