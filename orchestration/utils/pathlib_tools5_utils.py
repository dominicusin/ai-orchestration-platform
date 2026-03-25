"""Pathlib tools5 utilities"""

import pathlib


def path_glob(p, pattern):
    """Glob"""
    return pathlib.Path(p).glob(pattern)


def path_rglob(p, pattern):
    """Rglob"""
    return pathlib.Path(p).rglob(pattern)
