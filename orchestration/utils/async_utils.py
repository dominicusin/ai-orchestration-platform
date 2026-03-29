"""Async utilities"""

import asyncio
from collections.abc import Callable
from typing import Any


async def run_async(func: Callable, *args, **kwargs) -> Any:
    """Run sync function in async context"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


async def gather_tasks(tasks: list[asyncio.Task]) -> list[Any]:
    """Gather multiple async tasks"""
    return await asyncio.gather(*tasks, return_exceptions=True)


async def run_with_timeout(coro, timeout: float):
    """Run coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except TimeoutError:
        return None
