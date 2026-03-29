"""ABC utilities"""

import abc


def abstract_class(cls: type):
    """Mark class as abstract"""
    return abc.abstractmethod(cls)


def abstract_method(func):
    """Mark method as abstract"""
    return abc.abstractmethod(func)


def abstract_property(func):
    """Mark property as abstract"""
    return property(abc.abstractmethod(func))


def register_subclass(cls: type, subclass: type):
    """Register subclass for abstract class"""
    cls.register(subclass)
