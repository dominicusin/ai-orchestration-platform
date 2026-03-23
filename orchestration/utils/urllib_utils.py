"""URLlib utilities"""

import urllib.parse
from typing import Dict, Any


def url_encode(params: Dict) -> str:
    """URL encode parameters"""
    return urllib.parse.urlencode(params)


def url_decode(query: str) -> Dict:
    """URL decode query"""
    return dict(urllib.parse.parse_qsl(query))


def url_quote(text: str) -> str:
    """URL quote text"""
    return urllib.parse.quote(text)


def url_unquote(text: str) -> str:
    """URL unquote text"""
    return urllib.parse.unquote(text)


def url_join(base: str, *parts: str) -> str:
    """Join URL parts"""
    return urllib.parse.urljoin(base, '/'.join(parts))
