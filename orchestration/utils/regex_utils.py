"""Regex utilities"""

import re
from typing import List, Match


def regex_match(pattern: str, text: str) -> bool:
    """Check if pattern matches"""
    return bool(re.match(pattern, text))


def regex_search(pattern: str, text: str) -> Match:
    """Search for pattern"""
    return re.search(pattern, text)


def regex_findall(pattern: str, text: str) -> List[str]:
    """Find all matches"""
    return re.findall(pattern, text)


def regex_sub(pattern: str, repl: str, text: str) -> str:
    """Replace pattern"""
    return re.sub(pattern, repl, text)


def regex_split(pattern: str, text: str) -> List[str]:
    """Split by pattern"""
    return re.split(pattern, text)


def compile_pattern(pattern: str):
    """Compile regex pattern"""
    return re.compile(pattern)
