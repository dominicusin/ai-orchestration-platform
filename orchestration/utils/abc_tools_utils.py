"""ABC tools utilities"""

import abc


def abstractmethod_2(func):
    """Abstract method"""
    return abc.abstractmethod(func)


def abstractproperty_2(func):
    """Abstract property"""
    return property(abc.abstractmethod(func))
