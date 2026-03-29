"""Tests for Formatters"""

import pytest

from orchestration.formatters import (
    CSVFormatter,
    JSONFormatter,
    MarkdownFormatter,
    PrettyJSONFormatter,
    TableFormatter,
    TextFormatter,
    TimestampFormatter,
    XMLFormatter,
    get_formatter,
    to_csv,
    to_json,
    to_markdown,
    to_table,
    to_xml,
)


class TestJSONFormatter:
    """Test JSONFormatter"""

    def test_format_dict(self):
        """Test format dict"""
        f = JSONFormatter()
        result = f.format({"key": "value"})
        assert '"key"' in result

    def test_format_list(self):
        """Test format list"""
        f = JSONFormatter()
        result = f.format([1, 2, 3])
        assert "[" in result


class TestPrettyJSONFormatter:
    """Test PrettyJSONFormatter"""

    def test_format(self):
        """Test format"""
        f = PrettyJSONFormatter()
        result = f.format({"key": "value"})
        assert "key" in result


class TestTableFormatter:
    """Test TableFormatter"""

    def test_format_list_of_dicts(self):
        """Test format list of dicts"""
        f = TableFormatter()
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        result = f.format(data)
        assert "name" in result
        assert "John" in result

    def test_format_with_columns(self):
        """Test format with columns"""
        f = TableFormatter(columns=["name"])
        data = [{"name": "John", "age": 30}]
        result = f.format(data)
        assert "John" in result


class TestCSVFormatter:
    """Test CSVFormatter"""

    def test_format(self):
        """Test format"""
        f = CSVFormatter()
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        result = f.format(data)
        assert "name,age" in result
        assert "John,30" in result


class TestTextFormatter:
    """Test TextFormatter"""

    def test_format_dict(self):
        """Test format dict"""
        f = TextFormatter()
        result = f.format({"key": "value"})
        assert "key: value" in result

    def test_format_list(self):
        """Test format list"""
        f = TextFormatter()
        result = f.format(["a", "b", "c"])
        assert "a" in result


class TestMarkdownFormatter:
    """Test MarkdownFormatter"""

    def test_format_table(self):
        """Test format table"""
        f = MarkdownFormatter()
        data = [{"name": "John", "age": 30}]
        result = f.format(data)
        assert "|" in result
        assert "name" in result


class TestXMLFormatter:
    """Test XMLFormatter"""

    def test_format_list(self):
        """Test format list"""
        f = XMLFormatter()
        data = [{"name": "John"}]
        result = f.format(data)
        assert "<root>" in result
        assert "<name>John</name>" in result


class TestTimestampFormatter:
    """Test TimestampFormatter"""

    def test_format(self):
        """Test format"""
        f = TimestampFormatter(JSONFormatter(), fmt="%Y-%m-%d")
        result = f.format({"key": "value"})
        assert "key" in result
        assert "[" in result


class TestFactoryFunctions:
    """Test factory functions"""

    def test_get_formatter_json(self):
        """Test get formatter json"""
        f = get_formatter("json")
        assert isinstance(f, JSONFormatter)

    def test_get_formatter_table(self):
        """Test get formatter table"""
        f = get_formatter("table")
        assert isinstance(f, TableFormatter)

    def test_get_formatter_csv(self):
        """Test get formatter csv"""
        f = get_formatter("csv")
        assert isinstance(f, CSVFormatter)

    def test_get_formatter_unknown(self):
        """Test unknown formatter"""
        with pytest.raises(ValueError):
            get_formatter("unknown")

    def test_to_json(self):
        """Test to_json"""
        result = to_json({"key": "value"})
        assert "key" in result

    def test_to_table(self):
        """Test to_table"""
        result = to_table([{"name": "John"}])
        assert "John" in result

    def test_to_csv(self):
        """Test to_csv"""
        result = to_csv([{"name": "John"}])
        assert "name" in result

    def test_to_markdown(self):
        """Test to_markdown"""
        result = to_markdown([{"name": "John"}])
        assert "|" in result

    def test_to_xml(self):
        """Test to_xml"""
        result = to_xml([{"name": "John"}])
        assert "<name>John</name>" in result
