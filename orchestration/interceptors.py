"""Pipeline interceptors"""

import logging
from typing import Callable, Any

logger = logging.getLogger("orchestration.interceptors")


class Interceptor:
    """Base interceptor"""
    
    def intercept(self, chain: Callable, *args, **kwargs) -> Any:
        return chain(*args, **kwargs)


class LoggingInterceptor(Interceptor):
    """Logging interceptor"""
    
    def intercept(self, chain: Callable, *args, **kwargs) -> Any:
        logger.debug(f"Calling {chain.__name__}")
        result = chain(*args, **kwargs)
        logger.debug(f"Completed {chain.__name__}")
        return result


class TimingInterceptor(Interceptor):
    """Timing interceptor"""
    
    def intercept(self, chain: Callable, *args, **kwargs) -> Any:
        import time
        start = time.time()
        result = chain(*args, **kwargs)
        logger.debug(f"{chain.__name__} took {time.time() - start:.3f}s")
        return result


class InterceptorChain:
    """Chain of interceptors"""
    
    def __init__(self):
        self.interceptors = []
    
    def add(self, interceptor: Interceptor):
        self.interceptors.append(interceptor)
    
    def execute(self, chain: Callable, *args, **kwargs) -> Any:
        for interceptor in self.interceptors:
            chain = lambda *a, **kw: interceptor.intercept(chain, *a, **kw)
        return chain(*args, **kwargs)
