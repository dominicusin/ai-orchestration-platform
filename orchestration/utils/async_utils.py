"""Async utilities"""

import asyncio
from typing import Callable, Any, List


async def run_async(func: Callable, *args, **kwargs) -> Any:
    """Run sync function in async context"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


async def gather_tasks(tasks: List[asyncio.Task]) -> List[Any]:
    """Gather multiple async tasks"""
    return await asyncio.gather(*tasks, return_exceptions=True)


async def run_with_timeout(coro, timeout: float):
    """Run coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return None
