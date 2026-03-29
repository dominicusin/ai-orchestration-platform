"""Tests for Loaders"""

import csv
import json
import os
import tempfile

import pytest

from orchestration.loaders import (
    CSVLoader,
    DirectoryLoader,
    GlobLoader,
    JSONLoader,
    TextLoader,
    XMLLoader,
    get_loader,
    load_csv,
    load_json,
    load_text,
    load_xml,
)


class TestJSONLoader:
    """Test JSONLoader"""

    def test_load(self):
        """Test load"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            data = {"key": "value"}

            with open(path, "w") as f:
                json.dump(data, f)

            loader = JSONLoader()
            result = loader.load(path)
            assert result == data

    def test_load_lines(self):
        """Test load lines"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.jsonl")
            with open(path, "w") as f:
                f.write('{"a": 1}\n{"b": 2}\n')

            loader = JSONLoader()
            result = list(loader.load_lines(path))
            assert len(result) == 2


class TestCSVLoader:
    """Test CSVLoader"""

    def test_load(self):
        """Test load"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["name", "age"])
                writer.writerow(["John", "30"])
                writer.writerow(["Jane", "25"])

            loader = CSVLoader()
            result = loader.load(path)
            assert len(result) == 2
            assert result[0]["name"] == "John"


class TestXMLLoader:
    """Test XMLLoader"""

    def test_load(self):
        """Test load"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.xml")
            with open(path, "w") as f:
                f.write('<?xml version="1.0"?><root><item><name>John</name></item></root>')

            loader = XMLLoader()
            result = loader.load(path)
            assert len(result) == 1
            assert result[0]["name"] == "John"


class TestTextLoader:
    """Test TextLoader"""

    def test_load(self):
        """Test load"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            with open(path, "w") as f:
                f.write("Hello\nWorld")

            loader = TextLoader()
            result = loader.load(path)
            assert result == "Hello\nWorld"

    def test_load_lines(self):
        """Test load lines"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            with open(path, "w") as f:
                f.write("line1\nline2\n")

            loader = TextLoader()
            result = list(loader.load_lines(path))
            assert result == ["line1", "line2"]


class TestDirectoryLoader:
    """Test DirectoryLoader"""

    def test_load(self):
        """Test load"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files
            open(os.path.join(tmpdir, "file1.txt"), "w").close()
            open(os.path.join(tmpdir, "file2.txt"), "w").close()
            open(os.path.join(tmpdir, "file3.log"), "w").close()

            loader = DirectoryLoader(pattern="*.txt")
            result = loader.load(tmpdir)
            assert len(result) == 2


class TestGlobLoader:
    """Test GlobLoader"""

    def test_load(self):
        """Test load"""
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "file1.txt"), "w").close()
            open(os.path.join(tmpdir, "file2.txt"), "w").close()

            loader = GlobLoader("*.txt")
            result = loader.load(tmpdir)
            assert len(result) == 2


class TestFactoryFunctions:
    """Test factory functions"""

    def test_get_loader_json(self):
        """Test get loader json"""
        l = get_loader("json")
        assert isinstance(l, JSONLoader)

    def test_get_loader_csv(self):
        """Test get loader csv"""
        l = get_loader("csv")
        assert isinstance(l, CSVLoader)

    def test_get_loader_unknown(self):
        """Test unknown loader"""
        with pytest.raises(ValueError):
            get_loader("unknown")

    def test_load_json(self):
        """Test load json"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            with open(path, "w") as f:
                json.dump({"key": "value"}, f)

            result = load_json(path)
            assert result == {"key": "value"}

    def test_load_csv(self):
        """Test load csv"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["name"])
                writer.writerow(["John"])

            result = load_csv(path)
            assert len(result) == 1

    def test_load_xml(self):
        """Test load xml"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.xml")
            with open(path, "w") as f:
                f.write('<?xml version="1.0"?><root><item><name>John</name></item></root>')

            result = load_xml(path)
            assert len(result) == 1

    def test_load_text(self):
        """Test load text"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            with open(path, "w") as f:
                f.write("test content")

            result = load_text(path)
            assert result == "test content"
