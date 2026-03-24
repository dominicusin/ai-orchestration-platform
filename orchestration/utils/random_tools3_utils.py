"""Random tools3 utilities"""

import random


def shuffle_2(seq):
    """Shuffle"""
    result = seq.copy()
    random.shuffle(result)
    return result


def sample_2(population, k):
    """Sample"""
    return random.sample(population, k)
