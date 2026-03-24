"""Pathlib tools4 utilities"""

import pathlib


def path_write_text(p, text):
    """Write text"""
    pathlib.Path(p).write_text(text)


def path_iterdir(p):
    """Iterdir"""
    return pathlib.Path(p).iterdir()
