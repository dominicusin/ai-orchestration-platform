"""Itertools utilities"""

import itertools
from typing import List, Iterator, Callable


def pairwise(iterable: Iterator) -> Iterator:
    """ pairwise from itertools"""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def batched(iterable: Iterator, n: int) -> Iterator:
    """Batch iterator into chunks"""
    iterator = iter(iterable)
    while True:
        batch = list(itertools.islice(iterator, n))
        if not batch:
            break
        yield batch


def product(*iterables: List) -> Iterator:
    """Cartesian product"""
    return itertools.product(*iterables)


def permutations(items: List, r: int = None) -> Iterator:
    """Permutations"""
    return itertools.permutations(items, r)


def combinations(items: List, r: int) -> Iterator:
    """Combinations"""
    return itertools.combinations(items, r)


def cycle_func(func: Callable, times: int = None) -> Callable:
    """Cycle function results"""
    def cycled(*args, **kwargs):
        for _ in itertools.count() if times is None else range(times):
            yield func(*args, **kwargs)
    return cycled
