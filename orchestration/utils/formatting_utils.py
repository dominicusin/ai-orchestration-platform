```python
"""Formatting utilities"""

from typing import Any, Dict, List


def format_table(data: List[Dict], headers: List[str] = None) -> str:
    """Format data as table"""
    if not data:
        return ""
    
    if headers is None:
        headers = list(data[0].keys())
    
    col_widths = {h: len(h) for h in headers}
    for row in data:
        for h in headers:
            col_widths[h] = max(col_widths[h], len(str(row.get(h, ""))))
    
    lines = []
    header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
    lines.append(header_line)
    lines.append("-" * len(header_line))
    
    for row in data:
        line = " | ".join(str(row.get(h, "")).ljust(col_widths[h]) for h in headers)
        lines.append(line)
    
    return "\n".join(lines)


def format_bytes(size: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"


def format_percent(value: float, decimals: int = 1) -> str:
    """Format percentage"""
    return f"{value * 100:.{decimals}f}%"


def format_list(items: List[Any], sep: str = ", ", last_sep: str = " and ") -> str:
    """Format list as string"""
    if not items:
        return ""
    if len(items) == 1:
        return str(items[0])
    return sep.join(str(i) for i in items[:-1]) + last_sep + str(items[-1])
```