"""Batch processing utilities"""

from typing import Callable, List, Any, TypeVar, Iterator

T = TypeVar('T')
R = TypeVar('R')


def batch_items(items: List[T], batch_size: int) -> Iterator[List[T]]:
    """Split items into batches"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def process_batches(
    items: List[T],
    processor: Callable[[T], R],
    batch_size: int = 100,
    workers: int = 4,
) -> List[R]:
    """Process items in batches"""
    from concurrent.futures import ThreadPoolExecutor
    
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for batch in batch_items(items, batch_size):
            batch_results = list(executor.map(processor, batch))
            results.extend(batch_results)
    return results


def chunk_by_count(items: List[T], num_chunks: int) -> List[List[T]]:
    """Split items into roughly equal chunks"""
    if num_chunks <= 0 or not items:
        return []
    
    chunk_size = len(items) // num_chunks
    if chunk_size == 0:
        return [[item] for item in items] if num_chunks >= len(items) else [items]
    
    remainder = len(items) % num_chunks
    result = []
    idx = 0
    
    for i in range(num_chunks):
        size = chunk_size + (1 if i < remainder else 0)
        result.append(items[idx:idx + size])
        idx += size
    
    return result
