"""Random utilities"""

import random
from typing import List


def random_int_range(min_val: int, max_val: int) -> int:
    """Random integer in range"""
    return random.randint(min_val, max_val)


def random_float_range(min_val: float, max_val: float) -> float:
    """Random float in range"""
    return random.uniform(min_val, max_val)


def random_choice_list(items: List) -> any:
    """Random choice from list"""
    return random.choice(items)


def random_sample_list(items: List, k: int) -> List:
    """Random sample from list"""
    return random.sample(items, k)


def random_shuffle_list(items: List) -> List:
    """Shuffle list"""
    result = items.copy()
    random.shuffle(result)
    return result