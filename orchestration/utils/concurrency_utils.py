"""Concurrency utilities"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Callable, Any, List


def run_parallel(func: Callable, items: List[Any], workers: int = 4) -> List[Any]:
    """Run function in parallel on items"""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(func, items))


async def run_async_parallel(funcs: List[Callable], workers: int = 4) -> List[Any]:
    """Run async functions in parallel"""
    semaphore = asyncio.Semaphore(workers)
    
    async def limited_run(f):
        async with semaphore:
            return await f()
    
    return await asyncio.gather(*[limited_run(f) for f in funcs])


class Pool:
    """Worker pool"""
    
    def __init__(self, workers: int = 4, use_process: bool = False):
        self.workers = workers
        self.use_process = use_process
        self.pool = None
    
    def __enter__(self):
        cls = ProcessPoolExecutor if self.use_process else ThreadPoolExecutor
        self.pool = cls(max_workers=self.workers)
        return self.pool
    
    def __exit__(self, *args):
        if self.pool:
            self.pool.shutdown()
