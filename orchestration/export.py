"""
Export utilities
Утилиты для экспорта данных
"""

import csv
import json
import xml.etree.ElementTree as ET
from typing import Any


class Exporter:
    """Базовый класс экспортера"""

    def export(self, data: Any, path: str):
        """Экспорт данных"""
        raise NotImplementedError


class JSONExporter(Exporter):
    """Экспорт в JSON"""

    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def export(self, data: Any, path: str):
        """Экспорт в JSON файл"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=self.indent, ensure_ascii=self.ensure_ascii, default=str)


class CSVExporter(Exporter):
    """Экспорт в CSV"""

    def __init__(self, delimiter: str = ",", include_header: bool = True):
        self.delimiter = delimiter
        self.include_header = include_header

    def export(self, data: Any, path: str):
        """Экспорт в CSV файл"""
        if not isinstance(data, list) or not data:
            return

        with open(path, "w", encoding="utf-8", newline="") as f:
            if isinstance(data[0], dict):
                writer = csv.DictWriter(f, fieldnames=data[0].keys(), delimiter=self.delimiter)
                if self.include_header:
                    writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.writer(f, delimiter=self.delimiter)
                writer.writerows(data)


class XMLExporter(Exporter):
    """Экспорт в XML"""

    def __init__(self, root: str = "root", item: str = "item"):
        self.root = root
        self.item = item

    def export(self, data: Any, path: str):
        """Экспорт в XML файл"""
        root = ET.Element(self.root)

        if isinstance(data, list):
            for item in data:
                elem = ET.SubElement(root, self.item)
                if isinstance(item, dict):
                    for key, value in item.items():
                        child = ET.SubElement(elem, key)
                        child.text = str(value)
                else:
                    elem.text = str(item)

        tree = ET.ElementTree(root)
        tree.write(path, encoding="utf-8", xml_declaration=True)


class TextExporter(Exporter):
    """Экспорт в текст"""

    def __init__(self, separator: str = "\n"):
        self.separator = separator

    def export(self, data: Any, path: str):
        """Экспорт в текстовый файл"""
        with open(path, "w", encoding="utf-8") as f:
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        line = self.separator.join(f"{k}: {v}" for k, v in item.items())
                    else:
                        line = str(item)
                    f.write(line + "\n")
            elif isinstance(data, dict):
                for key, value in data.items():
                    f.write(f"{key}: {value}\n")
            else:
                f.write(str(data))


class MarkdownExporter(Exporter):
    """Экспорт в Markdown"""

    def export(self, data: Any, path: str):
        """Экспорт в Markdown файл"""
        lines = []

        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Table
            columns = list(data[0].keys())
            lines.append("| " + " | ".join(columns) + " |")
            lines.append("|" + "|".join("---" for _ in columns) + "|")

            for row in data:
                line = "| " + " | ".join(str(row.get(c, "")) for c in columns) + " |"
                lines.append(line)

        elif isinstance(data, dict):
            for key, value in data.items():
                lines.append(f"**{key}**: {value}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


# Factory functions

def get_exporter(format: str, **kwargs) -> Exporter:
    """Получение экспортера по формату"""
    exporters = {
        "json": JSONExporter,
        "csv": CSVExporter,
        "xml": XMLExporter,
        "text": TextExporter,
        "markdown": MarkdownExporter,
    }

    if format not in exporters:
        raise ValueError(f"Unknown format: {format}")

    return exporters[format](**kwargs)


def export_to_json(data: Any, path: str, **kwargs):
    """Экспорт в JSON"""
    JSONExporter(**kwargs).export(data, path)


def export_to_csv(data: Any, path: str, **kwargs):
    """Экспорт в CSV"""
    CSVExporter(**kwargs).export(data, path)


def export_to_xml(data: Any, path: str, **kwargs):
    """Экспорт в XML"""
    XMLExporter(**kwargs).export(data, path)


def export_to_text(data: Any, path: str, **kwargs):
    """Экспорт в текст"""
    TextExporter(**kwargs).export(data, path)


def export_to_markdown(data: Any, path: str):
    """Экспорт в Markdown"""
    MarkdownExporter().export(data, path)
