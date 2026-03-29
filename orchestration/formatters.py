import json
from datetime import datetime
from typing import Any


class Formatter:
    """Базовый класс форматтера"""

    def format(self, data: Any) -> str:
        """Форматирование данных"""
        raise NotImplementedError


class JSONFormatter(Formatter):
    """JSON форматтер"""

    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def format(self, data: Any) -> str:
        return json.dumps(data, indent=self.indent, ensure_ascii=self.ensure_ascii, default=str)


class PrettyJSONFormatter(Formatter):
    """Красивый JSON форматтер с цветами (без цветов для совместимости)"""

    def format(self, data: Any) -> str:
        return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str)


class TableFormatter(Formatter):
    """Табличный форматтер"""

    def __init__(self, columns: list = None):
        self.columns = columns or []

    def format(self, data: Any) -> str:
        if not isinstance(data, list) or not data:
            return str(data)

        # Determine columns
        if not self.columns:
            if isinstance(data[0], dict):
                self.columns = list(data[0].keys())
            else:
                self.columns = [f"Col{i}" for i in range(len(data[0]))]

        # Build table
        col_widths = {c: len(c) for c in self.columns}

        for row in data:
            if isinstance(row, dict):
                for col in self.columns:
                    val = str(row.get(col, ""))
                    col_widths[col] = max(col_widths[col], len(val))

        # Header
        header = " | ".join(c.ljust(col_widths[c]) for c in self.columns)
        separator = "-+-".join("-" * col_widths[c] for c in self.columns)

        # Rows
        rows = []
        for row in data:
            if isinstance(row, dict):
                row_str = " | ".join(str(row.get(c, "")).ljust(col_widths[c]) for c in self.columns)
            else:
                row_str = " | ".join(str(v).ljust(col_widths[c]) for c, v in zip(self.columns, row))
            rows.append(row_str)

        return "\n".join([header, separator] + rows)


class CSVFormatter(Formatter):
    """CSV форматтер"""

    def __init__(self, delimiter: str = ",", include_header: bool = True):
        self.delimiter = delimiter
        self.include_header = include_header

    def format(self, data: Any) -> str:
        if not isinstance(data, list) or not data:
            return str(data)

        lines = []

        # Header
        if self.include_header and isinstance(data[0], dict):
            header = self.delimiter.join(data[0].keys())
            lines.append(header)

        # Rows
        for row in data:
            if isinstance(row, dict):
                line = self.delimiter.join(str(v) for v in row.values())
            else:
                line = self.delimiter.join(str(v) for v in row)
            lines.append(line)

        return "\n".join(lines)


class TextFormatter(Formatter):
    """Текстовый форматтер"""

    def format(self, data: Any) -> str:
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            return "\n".join(str(item) for item in data)
        return str(data)


class MarkdownFormatter(Formatter):
    """Markdown форматтер"""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Table
            columns = list(data[0].keys())
            lines = []

            # Header
            lines.append("| " + " | ".join(columns) + " |")
            lines.append("|" + "|".join("---" for _ in columns) + "|")

            # Rows
            for row in data:
                line = "| " + " | ".join(str(row.get(c, "")) for c in columns) + " |"
                lines.append(line)

            return "\n".join(lines)
        elif isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"**{key}**: {value}")
            return "\n".join(lines)
        return str(data)


class XMLFormatter(Formatter):
    """XML форматтер"""

    def __init__(self, root: str = "root", item: str = "item"):
        self.root = root
        self.item = item

    def format(self, data: Any) -> str:
        lines = [f"<{self.root}>"]

        if isinstance(data, list):
            for item in data:
                lines.append(f"  <{self.item}>")
                if isinstance(item, dict):
                    for key, value in item.items():
                        lines.append(f"    <{key}>{value}</{key}>")
                else:
                    lines.append(f"    {item}")
                lines.append(f"  </{self.item}>")
        elif isinstance(data, dict):
            for key, value in data.items():
                lines.append(f"  <{key}>{value}</{key}>")

        lines.append(f"</{self.root}>")
        return "\n".join(lines)


class TimestampFormatter(Formatter):
    """Форматтер с timestamp"""

    def __init__(self, formatter: Formatter, fmt: str = "%Y-%m-%d %H:%M:%S"):
        self.formatter = formatter
        self.fmt = fmt

    def format(self, data: Any) -> str:
        timestamp = datetime.now().strftime(self.fmt)
        formatted = self.formatter.format(data)
        return f"[{timestamp}]\n{formatted}"


# Factory functions

def get_formatter(format: str, **kwargs) -> Formatter:
    """Получение форматтера по типу"""
    formatters = {
        "json": JSONFormatter,
        "pretty_json": PrettyJSONFormatter,
        "table": TableFormatter,
        "csv": CSVFormatter,
        "text": TextFormatter,
        "markdown": MarkdownFormatter,
        "xml": XMLFormatter,
    }

    if format not in formatters:
        raise ValueError(f"Unknown format: {format}")

    return formatters[format](**kwargs)


def to_json(data: Any, **kwargs) -> str:
    """Форматирование в JSON"""
    return JSONFormatter(**kwargs).format(data)


def to_table(data: Any, **kwargs) -> str:
    """Форматирование в таблицу"""
    return TableFormatter(**kwargs).format(data)


def to_csv(data: Any, **kwargs) -> str:
    """Форматирование в CSV"""
    return CSVFormatter(**kwargs).format(data)


def to_markdown(data: Any) -> str:
    """Форматирование в Markdown"""
    return MarkdownFormatter().format(data)


def to_xml(data: Any, **kwargs) -> str:
    """Форматирование в XML"""
    return XMLFormatter(**kwargs).format(data)
