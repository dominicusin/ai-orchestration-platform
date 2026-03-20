"""String utilities"""

import re
from typing import List


def slugify(text: str) -> str:
    """Convert text to slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def truncate(text: str, length: int, suffix: str = "...") -> str:
    """Truncate text"""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def camel_to_snake(text: str) -> str:
    """camelCase to snake_case"""
    return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()


def snake_to_camel(text: str) -> str:
    """snake_case to camelCase"""
    components = text.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def extract_numbers(text: str) -> List[int]:
    """Extract numbers from text"""
    return [int(n) for n in re.findall(r'\d+', text)]


def mask_sensitive(text: str) -> str:
    """Mask sensitive data"""
    if len(text) <= 4:
        return '*' * len(text)
    return text[:2] + '*' * (len(text) - 4) + text[-2:]
