"""Heapq tools5 utilities"""

import heapq


def heapify_3(heap):
    """Heapify"""
    heapq.heapify(heap)


def heapreplace_3(heap, item):
    """Heapreplace"""
    return heapq.heapreplace(heap, item)
