"""Random utilities"""

import random
import string
from typing import List


def random_int(min_val: int = 0, max_val: int = 100) -> int:
    """Random integer"""
    return random.randint(min_val, max_val)


def random_float(min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Random float"""
    return random.uniform(min_val, max_val)


def random_string(length: int = 10, charset: str = None) -> str:
    """Random string"""
    if charset is None:
        charset = string.ascii_letters + string.digits
    return ''.join(random.choice(charset) for _ in range(length))


def random_choice(choices: List) -> any:
    """Random choice"""
    return random.choice(choices)


def random_shuffle(items: List) -> List:
    """Random shuffle"""
    result = items.copy()
    random.shuffle(result)
    return result


def random_bool() -> bool:
    """Random boolean"""
    return random.choice([True, False])
