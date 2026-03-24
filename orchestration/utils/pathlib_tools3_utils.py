"""Pathlib tools3 utilities"""

import pathlib


def path_is_dir(p):
    """Is directory"""
    return pathlib.Path(p).is_dir()


def path_read_text(p):
    """Read text"""
    return pathlib.Path(p).read_text()
