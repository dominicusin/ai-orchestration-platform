"""Pathlib tools utilities"""

import pathlib


def path_cwd():
    """Current directory"""
    return pathlib.Path.cwd()


def path_home():
    """Home directory"""
    return pathlib.Path.home()
