"""URL utilities"""

import urllib.parse


def parse_url(url: str) -> dict[str, str]:
    """Parse URL into components"""
    parsed = urllib.parse.urlparse(url)
    return {
        "scheme": parsed.scheme,
        "netloc": parsed.netloc,
        "path": parsed.path,
        "params": parsed.params,
        "query": dict(urllib.parse.parse_qsl(parsed.query)),
        "fragment": parsed.fragment,
    }


def build_url(scheme: str, host: str, path: str = "", params: dict = None) -> str:
    """Build URL from components"""
    query = urllib.parse.urlencode(params) if params else ""
    return f"{scheme}://{host}{path}?{query}" if query else f"{scheme}://{host}{path}"


def encode_params(params: dict) -> str:
    """URL encode parameters"""
    return urllib.parse.urlencode(params)


def decode_params(query: str) -> dict:
    """Decode URL parameters"""
    return dict(urllib.parse.parse_qsl(query))


def get_domain(url: str) -> str | None:
    """Extract domain from URL"""
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc or None
