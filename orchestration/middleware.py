"""API middleware for request/response processing"""

import os
import time
import logging
import hashlib
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

logger = logging.getLogger("orchestration.middleware")


@dataclass
class Request:
    """HTTP request"""
    method: str
    path: str
    headers: Dict[str, str]
    body: Any
    query_params: Dict[str, str]
    client_ip: str = ""


@dataclass
class Response:
    """HTTP response"""
    status_code: int
    body: Any
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class Middleware:
    """Base middleware class"""
    
    async def process_request(self, request: Request) -> Request:
        """Process request"""
        return request
    
    async def process_response(self, response: Response, request: Request) -> Response:
        """Process response"""
        return response


class LoggingMiddleware(Middleware):
    """Log requests and responses"""
    
    async def process_request(self, request: Request) -> Request:
        logger.info(f"{request.method} {request.path}")
        return request
    
    async def process_response(self, response: Response, request: Request) -> Response:
        logger.info(f"{request.method} {request.path} -> {response.status_code}")
        return response


class TimingMiddleware(Middleware):
    """Add timing headers"""
    
    def __init__(self):
        self.start_times: Dict[str, float] = {}
    
    async def process_request(self, request: Request) -> Request:
        request_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.start_times[request_id] = time.time()
        request.headers["X-Request-ID"] = request_id
        return request
    
    async def process_response(self, response: Response, request: Request) -> Response:
        request_id = request.headers.get("X-Request-ID")
        
        if request_id and request_id in self.start_times:
            duration = time.time() - self.start_times[request_id]
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            del self.start_times[request_id]
        
        return response


class CorsMiddleware(Middleware):
    """Handle CORS"""
    
    def __init__(
        self,
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
    
    async def process_request(self, request: Request) -> Request:
        # Handle preflight
        if request.method == "OPTIONS":
            # Would handle preflight here
            pass
        return request
    
    async def process_response(self, response: Response, request: Request) -> Response:
        response.headers["Access-Control-Allow-Origin"] = ", ".join(self.allow_origins)
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        return response


class RateLimitMiddleware(Middleware):
    """Rate limiting"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    async def process_request(self, request: Request) -> Request:
        client_id = request.client_ip or "default"
        
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id]
                if t > minute_ago
            ]
        else:
            self.requests[client_id] = []
        
        # Check limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            raise Exception("Rate limit exceeded")
        
        self.requests[client_id].append(now)
        
        return request


class AuthMiddleware(Middleware):
    """Authentication"""
    
    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
    
    async def process_request(self, request: Request) -> Request:
        # Check API key
        api_key = request.headers.get("X-API-Key")
        
        if api_key and api_key in self.api_keys:
            return request
        
        # Allow unauthenticated for some paths
        if request.path in ["/health", "/docs", "/openapi.json"]:
            return request
        
        raise Exception("Unauthorized")


class CompressionMiddleware(Middleware):
    """Compress responses"""
    
    async def process_response(self, response: Response, request: Request) -> Response:
        # Check if client accepts gzip
        accept_encoding = request.headers.get("Accept-Encoding", "")
        
        if "gzip" in accept_encoding and isinstance(response.body, str):
            import gzip
            
            compressed = gzip.compress(response.body.encode())
            response.body = compressed
            response.headers["Content-Encoding"] = "gzip"
        
        return response


class CacheMiddleware(Middleware):
    """Cache responses"""
    
    def __init__(self):
        self.cache: Dict[str, tuple] = {}  # key -> (response, timestamp)
        self.ttl = 300  # 5 minutes
    
    async def process_request(self, request: Request) -> Request:
        # Check cache
        cache_key = f"{request.method}:{request.path}"
        
        if request.method == "GET" and cache_key in self.cache:
            response, timestamp = self.cache[cache_key]
            
            if time.time() - timestamp < self.ttl:
                # Return cached response
                # Would modify flow to return cached
                pass
        
        return request
    
    async def process_response(self, response: Response, request: Request) -> Response:
        # Cache GET requests
        if request.method == "GET" and response.status_code == 200:
            cache_key = f"{request.method}:{request.path}"
            self.cache[cache_key] = (response, time.time())
        
        return response


class MiddlewareChain:
    """Chain of middleware"""
    
    def __init__(self):
        self.middlewares: list = []
    
    def add(self, middleware: Middleware):
        """Add middleware to chain"""
        self.middlewares.append(middleware)
    
    async def process_request(self, request: Request) -> Request:
        """Process request through middleware"""
        for middleware in self.middlewares:
            request = await middleware.process_request(request)
        return request
    
    async def process_response(self, response: Response, request: Request) -> Response:
        """Process response through middleware"""
        for middleware in reversed(self.middlewares):
            response = await middleware.process_response(response, request)
        return response


def create_default_middleware_chain() -> MiddlewareChain:
    """Create default middleware chain"""
    chain = MiddlewareChain()
    
    chain.add(LoggingMiddleware())
    chain.add(TimingMiddleware())
    chain.add(CorsMiddleware())
    chain.add(RateLimitMiddleware(requests_per_minute=60))
    chain.add(CacheMiddleware())
    
    return chain


# Decorator for middleware
def use_middleware(middleware: Middleware):
    """Decorator to add middleware to a handler"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request):
            # Process request
            request = await middleware.process_request(request)
            
            # Call handler
            response = await func(request)
            
            # Process response
            response = await middleware.process_response(response, request)
            
            return response
        return wrapper
    return decorator
