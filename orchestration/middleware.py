"""Middleware for DAG execution"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("orchestration.middleware")


@dataclass
class MiddlewareContext:
    """Context passed through middleware"""
    task_id: str
    data: Any
    metadata: dict = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)


class Middleware:
    """Base middleware"""

    def process(self, context: MiddlewareContext, next_handler: Callable) -> Any:
        """Process request"""
        raise NotImplementedError


class LoggingMiddleware(Middleware):
    """Log task execution"""

    def process(self, context: MiddlewareContext, next_handler: Callable) -> Any:
        logger.info(f"Starting task: {context.task_id}")

        try:
            result = next_handler(context)
            logger.info(f"Completed task: {context.task_id}")
            return result
        except Exception as e:
            logger.error(f"Task {context.task_id} failed: {e}")
            raise


class TimingMiddleware(Middleware):
    """Measure execution time"""

    def process(self, context: MiddlewareContext, next_handler: Callable) -> Any:
        start = time.time()

        result = next_handler(context)

        duration = time.time() - start
        context.metadata["duration"] = duration

        return result


class ValidationMiddleware(Middleware):
    """Validate input"""

    def __init__(self, validator: Callable):
        self.validator = validator

    def process(self, context: MiddlewareContext, next_handler: Callable) -> Any:
        if not self.validator(context.data):
            raise ValueError(f"Validation failed for {context.task_id}")

        return next_handler(context)


class RetryMiddleware(Middleware):
    """Retry on failure"""

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    def process(self, context: MiddlewareContext, next_handler: Callable) -> Any:
        last_error = None

        for attempt in range(self.max_attempts):
            try:
                return next_handler(context)
            except Exception as e:
                last_error = e
                if attempt < self.max_attempts - 1:
                    logger.warning(f"Retry {attempt + 1} for {context.task_id}")

        raise last_error


class CachingMiddleware(Middleware):
    """Cache results"""

    def __init__(self):
        self.cache: dict[str, Any] = {}

    def process(self, context: MiddlewareContext, next_handler: Callable) -> Any:
        cache_key = f"{context.task_id}:{hash(str(context.data))}"

        if cache_key in self.cache:
            logger.debug(f"Cache hit for {context.task_id}")
            return self.cache[cache_key]

        result = next_handler(context)
        self.cache[cache_key] = result

        return result


class MiddlewareChain:
    """Chain of middlewares"""

    def __init__(self):
        self.middlewares: list[Middleware] = []

    def add(self, middleware: Middleware):
        self.middlewares.append(middleware)

    def execute(self, context: MiddlewareContext) -> Any:
        """Execute middlewares in order"""

        def final_handler(ctx):
            return ctx.data

        # Build chain (reverse order)
        handler = final_handler
        for middleware in reversed(self.middlewares):

            def make_wrapper(m, h):
                def wrapper(ctx):
                    return m.process(ctx, h)
                return wrapper

            handler = make_wrapper(middleware, handler)

        return handler(context)


def create_middleware_chain(config: dict) -> MiddlewareChain:
    """Create middleware chain from config"""
    chain = MiddlewareChain()

    if config.get("logging"):
        chain.add(LoggingMiddleware())

    if config.get("timing"):
        chain.add(TimingMiddleware())

    if config.get("caching"):
        chain.add(CachingMiddleware())

    if config.get("retry"):
        chain.add(RetryMiddleware(config.get("max_attempts", 3)))

    return chain
