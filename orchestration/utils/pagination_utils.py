"""Pagination utilities"""

from typing import Any


def paginate(items: list[Any], page: int, page_size: int) -> tuple[list[Any], int]:
    """Paginate items"""
    total_pages = (len(items) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total_pages


def paginate_generator(items: list[Any], page_size: int):
    """Generate pages"""
    for i in range(0, len(items), page_size):
        yield items[i:i + page_size]


class Paginator:
    """Paginator class"""

    def __init__(self, items: list[Any], page_size: int = 10):
        self.items = items
        self.page_size = page_size
        self.total = len(items)
        self.total_pages = (self.total + page_size - 1) // page_size

    def get_page(self, page: int) -> list[Any]:
        if page < 1 or page > self.total_pages:
            return []
        start = (page - 1) * self.page_size
        return self.items[start:start + self.page_size]

    def has_next(self, page: int) -> bool:
        return page < self.total_pages

    def has_prev(self, page: int) -> bool:
        return page > 1
