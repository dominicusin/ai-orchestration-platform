"""Version utilities"""

import re


def parse_version(version: str) -> tuple[int, ...]:
    """Parse version string to tuple"""
    return tuple(int(x) for x in re.findall(r'\d+', version))


def compare_versions(v1: str, v2: str) -> int:
    """Compare versions: -1, 0, 1"""
    p1, p2 = parse_version(v1), parse_version(v2)
    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1
    return 0


def is_compatible(current: str, required: str) -> bool:
    """Check if version is compatible"""
    return compare_versions(current, required) >= 0


def format_version(major: int, minor: int, patch: int = 0) -> str:
    """Format version string"""
    return f"{major}.{minor}.{patch}"
