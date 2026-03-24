"""Heapq tools2 utilities"""

import heapq


def heappush_2(heap, item):
    """Heappush"""
    heapq.heappush(heap, item)


def heappop_2(heap):
    """Heappop"""
    return heapq.heappop(heap)
