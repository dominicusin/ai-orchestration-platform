"""Pathlib tools6 utilities"""

import pathlib


def path_join(p, *parts):
    """Join path"""
    return pathlib.Path(p).joinpath(*parts)


def path_name(p):
    """Get name"""
    return pathlib.Path(p).name
