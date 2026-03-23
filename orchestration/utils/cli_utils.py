"""CLI utilities"""

import sys
from typing import Optional


def print_error(message: str):
    """Print error message"""
    print(f"ERROR: {message}", file=sys.stderr)


def print_warning(message: str):
    """Print warning message"""
    print(f"WARNING: {message}", file=sys.stderr)


def print_success(message: str):
    """Print success message"""
    print(f"✓ {message}")


def confirm(prompt: str, default: bool = False) -> bool:
    """Ask for confirmation"""
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        response = input(prompt + suffix).lower().strip()
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Please answer y or n")


def progress_bar(current: int, total: int, width: int = 40) -> str:
    """Generate progress bar"""
    percent = current / total
    filled = int(width * percent)
    return f"[{'█' * filled}{'░' * (width - filled)}] {int(percent * 100)}%"
