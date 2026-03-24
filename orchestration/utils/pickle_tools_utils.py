"""Pickle tools utilities"""

import pickle


def pickle_dump(obj, file):
    """Pickle dump"""
    pickle.dump(obj, file)


def pickle_load(file):
    """Pickle load"""
    return pickle.load(file)
