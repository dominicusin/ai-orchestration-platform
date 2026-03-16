"""Pipeline time utilities"""

import time
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger("orchestration.timing")


class Timer:
    """Timer utility"""
    
    def __init__(self, name: str = "timer"):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start(self):
        self.start_time = time.time()
    
    def stop(self):
        self.end_time = time.time()
    
    @property
    def elapsed(self) -> float:
        if self.start_time:
            end = self.end_time or time.time()
            return end - self.start_time
        return 0


@contextmanager
def timed(name: str = "operation"):
    """Context manager for timing"""
    timer = Timer(name)
    timer.start()
    try:
        yield timer
    finally:
        timer.stop()
        logger.debug(f"{name} took {timer.elapsed:.3f}s")
