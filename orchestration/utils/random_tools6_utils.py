"""Random tools6 utilities"""

import random


def shuffle_3(seq):
    """Shuffle"""
    result = seq.copy()
    random.shuffle(result)
    return result


def sample_3(population, k):
    """Sample"""
    return random.sample(population, k)
