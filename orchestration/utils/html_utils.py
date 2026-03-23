"""HTML utilities"""

import html
from typing import Dict


def html_escape(text: str) -> str:
    """Escape HTML"""
    return html.escape(text)


def html_unescape(text: str) -> str:
    """Unescape HTML"""
    return html.unescape(text)


def strip_tags(html_text: str) -> str:
    """Strip HTML tags"""
    import re
    return re.sub(r'<[^>]+>', '', html_text)


def parse_attr(attr_str: str) -> Dict[str, str]:
    """Parse HTML attributes"""
    import re
    pattern = r'(\w+)="([^"]*)"'
    return dict(re.findall(pattern, attr_str))
