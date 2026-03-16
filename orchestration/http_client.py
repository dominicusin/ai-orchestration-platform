"""HTTP client utilities"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("orchestration.http_client")


@dataclass
class HTTPResponse:
    """HTTP response"""
    status_code: int
    headers: Dict[str, str]
    body: Any
    elapsed_ms: float


class HTTPClient:
    """Async HTTP client with retry and timeout"""
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def get(
        self,
        url: str,
        headers: Dict = None,
        params: Dict = None,
    ) -> HTTPResponse:
        """GET request"""
        return await self._request("GET", url, headers=headers, params=params)
    
    async def post(
        self,
        url: str,
        data: Any = None,
        json: Dict = None,
        headers: Dict = None,
    ) -> HTTPResponse:
        """POST request"""
        return await self._request(
            "POST", url, data=data, json=json, headers=headers
        )
    
    async def put(
        self,
        url: str,
        data: Any = None,
        json: Dict = None,
        headers: Dict = None,
    ) -> HTTPResponse:
        """PUT request"""
        return await self._request(
            "PUT", url, data=data, json=json, headers=headers
        )
    
    async def delete(
        self,
        url: str,
        headers: Dict = None,
    ) -> HTTPResponse:
        """DELETE request"""
        return await self._request("DELETE", url, headers=headers)
    
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> HTTPResponse:
        """Make HTTP request with retry"""
        import aiohttp
        import time
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                start = time.time()
                
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        timeout=self.timeout,
                        **kwargs,
                    ) as response:
                        body = await response.text()
                        
                        # Try to parse JSON
                        try:
                            import json
                            body = json.loads(body)
                        except:
                            pass
                        
                        elapsed = (time.time() - start) * 1000
                        
                        return HTTPResponse(
                            status_code=response.status,
                            headers=dict(response.headers),
                            body=body,
                            elapsed_ms=elapsed,
                        )
            
            except asyncio.TimeoutError:
                last_error = "Timeout"
                logger.warning(f"Request timeout (attempt {attempt + 1})")
            
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Request error: {e}")
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        raise Exception(f"Request failed after {self.max_retries} attempts: {last_error}")


# Global client
_http_client: Optional[HTTPClient] = None


def get_http_client() -> HTTPClient:
    """Get HTTP client"""
    global _http_client
    if _http_client is None:
        _http_client = HTTPClient()
    return _http_client
