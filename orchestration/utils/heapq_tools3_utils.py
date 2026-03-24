"""Heapq tools3 utilities"""

import heapq


def heapify_2(heap):
    """Heapify"""
    heapq.heapify(heap)


def heapreplace_2(heap, item):
    """Heapreplace"""
    return heapq.heapreplace(heap, item)
