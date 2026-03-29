"""HTTP client for external APIs"""

import json
import logging
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("orchestration.http_client")


class HTTPClient:
    """HTTP client"""

    def __init__(self, base_url: str = "", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        headers: dict = None,
        body: Any = None,
    ) -> dict:
        """Make HTTP request"""
        url = f"{self.base_url}{path}"

        data = json.dumps(body).encode() if body else None

        req = urllib.request.Request(
            url,
            data=data,
            headers=headers or {},
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return {
                    "status": resp.status,
                    "body": json.loads(resp.read()),
                }
        except urllib.error.HTTPError as e:
            return {
                "status": e.code,
                "error": e.read().decode(),
            }

    def get(self, path: str, headers: dict = None) -> dict:
        return self.request("GET", path, headers)

    def post(self, path: str, body: Any = None, headers: dict = None) -> dict:
        return self.request("POST", path, headers, body)

    def put(self, path: str, body: Any = None, headers: dict = None) -> dict:
        return self.request("PUT", path, headers, body)

    def delete(self, path: str, headers: dict = None) -> dict:
        return self.request("DELETE", path, headers)
