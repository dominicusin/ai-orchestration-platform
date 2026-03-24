"""Pathlib tools2 utilities"""

import pathlib


def path_exists(p):
    """Path exists"""
    return pathlib.Path(p).exists()


def path_is_file(p):
    """Is file"""
    return pathlib.Path(p).is_file()
