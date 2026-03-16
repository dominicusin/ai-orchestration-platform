"""Pipeline filters for data processing"""

import re
import logging
from typing import Any, List, Callable

logger = logging.getLogger("orchestration.filters")


class Filter:
    """Base filter"""
    
    def apply(self, data: Any) -> Any:
        """Apply filter"""
        raise NotImplementedError


class TextFilter(Filter):
    """Filter text content"""
    
    def __init__(self, remove_patterns: List[str] = None):
        self.remove_patterns = remove_patterns or []
    
    def apply(self, text: str) -> str:
        for pattern in self.remove_patterns:
            text = re.sub(pattern, "", text)
        return text


class HTMLFilter(Filter):
    """Filter HTML content"""
    
    def apply(self, html: str) -> str:
        # Remove HTML tags
        html = re.sub(r"<[^>]+>", "", html)
        # Remove extra whitespace
        html = re.sub(r"\s+", " ", html)
        return html.strip()


class JSONFilter(Filter):
    """Filter JSON data"""
    
    def __init__(self, remove_keys: List[str] = None):
        self.remove_keys = remove_keys or []
    
    def apply(self, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        
        result = data.copy()
        
        for key in self.remove_keys:
            if key in result:
                del result[key]
        
        return result


class FilterChain:
    """Chain multiple filters"""
    
    def __init__(self):
        self.filters: List[Filter] = []
    
    def add(self, filter: Filter):
        """Add filter"""
        self.filters.append(filter)
    
    def apply(self, data: Any) -> Any:
        """Apply all filters"""
        for filter in self.filters:
            data = filter.apply(data)
        return data


def create_filter_chain(filters: List[str]) -> FilterChain:
    """Create filter chain from config"""
    chain = FilterChain()
    
    for filter_name in filters:
        if filter_name == "text":
            chain.add(TextFilter())
        elif filter_name == "html":
            chain.add(HTMLFilter())
        elif filter_name == "json":
            chain.add(JSONFilter())
    
    return chain
