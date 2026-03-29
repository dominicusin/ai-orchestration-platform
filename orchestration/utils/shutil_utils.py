"""Shutil utilities"""

import shutil


def copy_file(src: str, dst: str):
    """Copy file"""
    shutil.copy2(src, dst)


def copy_tree(src: str, dst: str):
    """Copy directory tree"""
    shutil.copytree(src, dst)


def move_file(src: str, dst: str):
    """Move file"""
    shutil.move(src, dst)


def remove_tree(path: str):
    """Remove directory tree"""
    shutil.rmtree(path)


def make_archive(base_name: str, format: str, root_dir: str):
    """Make archive"""
    return shutil.make_archive(base_name, format, root_dir)


def unpack_archive(archive: str, extract_dir: str):
    """Unpack archive"""
    shutil.unpack_archive(archive, extract_dir)
