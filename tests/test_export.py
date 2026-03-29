"""Tests for Export"""

import csv
import json
import os
import tempfile

import pytest

from orchestration.export import (
    CSVExporter,
    JSONExporter,
    MarkdownExporter,
    TextExporter,
    XMLExporter,
    export_to_csv,
    export_to_json,
    export_to_markdown,
    export_to_text,
    export_to_xml,
    get_exporter,
)


class TestJSONExporter:
    """Test JSONExporter"""

    def test_export(self):
        """Test export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            data = {"key": "value", "number": 42}

            exporter = JSONExporter()
            exporter.export(data, path)

            with open(path) as f:
                result = json.load(f)
            assert result == data


class TestCSVExporter:
    """Test CSVExporter"""

    def test_export_dict(self):
        """Test export dict"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]

            exporter = CSVExporter()
            exporter.export(data, path)

            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["name"] == "John"


class TestXMLExporter:
    """Test XMLExporter"""

    def test_export(self):
        """Test export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.xml")
            data = [{"name": "John"}, {"name": "Jane"}]

            exporter = XMLExporter()
            exporter.export(data, path)

            with open(path) as f:
                content = f.read()
            assert "<name>John</name>" in content


class TestTextExporter:
    """Test TextExporter"""

    def test_export_dict(self):
        """Test export dict"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            data = [{"name": "John", "age": 30}]

            exporter = TextExporter()
            exporter.export(data, path)

            with open(path) as f:
                content = f.read()
            assert "name" in content


class TestMarkdownExporter:
    """Test MarkdownExporter"""

    def test_export(self):
        """Test export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.md")
            data = [{"name": "John", "age": 30}]

            exporter = MarkdownExporter()
            exporter.export(data, path)

            with open(path) as f:
                content = f.read()
            assert "|" in content
            assert "name" in content


class TestFactoryFunctions:
    """Test factory functions"""

    def test_get_exporter_json(self):
        """Test get exporter json"""
        e = get_exporter("json")
        assert isinstance(e, JSONExporter)

    def test_get_exporter_csv(self):
        """Test get exporter csv"""
        e = get_exporter("csv")
        assert isinstance(e, CSVExporter)

    def test_get_exporter_unknown(self):
        """Test unknown exporter"""
        with pytest.raises(ValueError):
            get_exporter("unknown")

    def test_export_to_json(self):
        """Test export to json"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            export_to_json({"key": "value"}, path)
            assert os.path.exists(path)

    def test_export_to_csv(self):
        """Test export to csv"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            export_to_csv([{"name": "John"}], path)
            assert os.path.exists(path)

    def test_export_to_xml(self):
        """Test export to xml"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.xml")
            export_to_xml([{"name": "John"}], path)
            assert os.path.exists(path)

    def test_export_to_text(self):
        """Test export to text"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            export_to_text({"key": "value"}, path)
            assert os.path.exists(path)

    def test_export_to_markdown(self):
        """Test export to markdown"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.md")
            export_to_markdown([{"name": "John"}], path)
            assert os.path.exists(path)
