"""Heapq tools4 utilities"""

import heapq


def heappush_3(heap, item):
    """Heappush"""
    heapq.heappush(heap, item)


def heappop_3(heap):
    """Heappop"""
    return heapq.heappop(heap)
