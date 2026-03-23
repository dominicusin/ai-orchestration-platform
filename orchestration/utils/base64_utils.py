"""Base64 utilities"""

import base64
from typing import Union


def b64_encode(data: Union[str, bytes]) -> str:
    """Encode to base64"""
    if isinstance(data, str):
        data = data.encode()
    return base64.b64encode(data).decode()


def b64_decode(data: str) -> bytes:
    """Decode from base64"""
    return base64.b64decode(data)


def b64_encode_url(data: Union[str, bytes]) -> str:
    """URL-safe base64 encode"""
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).decode()


def b64_decode_url(data: str) -> bytes:
    """URL-safe base64 decode"""
    return base64.urlsafe_b64decode(data)
