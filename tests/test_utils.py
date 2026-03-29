"""Tests for utils"""

from orchestration.utils.collection_utils import group_by, unique
from orchestration.utils.enum_utils import enum_names, enum_values
from orchestration.utils.formatting_utils import format_bytes, format_percent
from orchestration.utils.math_utils import clamp_val, lerp_val
from orchestration.utils.string_utils import slugify, truncate


class TestEnumUtils:
    """Test enum utilities"""

    def test_enum_values(self):
        """Test get enum values"""
        from enum import Enum

        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"

        values = enum_values(Color)
        assert "red" in values
        assert "green" in values
        assert "blue" in values

    def test_enum_names(self):
        """Test get enum names"""
        from enum import Enum

        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        names = enum_names(Color)
        assert "RED" in names
        assert "GREEN" in names
        assert "BLUE" in names


class TestFormattingUtils:
    """Test formatting utilities"""

    def test_format_bytes(self):
        """Test bytes formatting"""
        assert "B" in format_bytes(100)
        assert "KB" in format_bytes(1024)
        assert "MB" in format_bytes(1048576)

    def test_format_percent(self):
        """Test percent formatting"""
        assert "50.0%" in format_percent(0.5)
        assert "100.0%" in format_percent(1.0)


class TestStringUtils:
    """Test string utilities"""

    def test_truncate(self):
        """Test truncate"""
        assert "..." in truncate("hello world", 5)
        assert truncate("hi", 10) == "hi"

    def test_slugify(self):
        """Test slugify"""
        assert "hello-world" in slugify("Hello World!")


class TestMathUtils:
    """Test math utilities"""

    def test_clamp_val(self):
        """Test clamp"""
        assert clamp_val(5, 0, 10) == 5
        assert clamp_val(-1, 0, 10) == 0
        assert clamp_val(100, 0, 10) == 10

    def test_lerp_val(self):
        """Test lerp"""
        assert lerp_val(0, 10, 0.5) == 5


class TestCollectionUtils:
    """Test collection utilities"""

    def test_group_by(self):
        """Test group by"""
        data = [{"type": "a", "val": 1}, {"type": "b", "val": 2}, {"type": "a", "val": 3}]
        grouped = group_by(data, "type")
        assert len(grouped["a"]) == 2

    def test_unique(self):
        """Test unique"""
        assert unique([1, 2, 2, 3, 3, 3]) == [1, 2, 3]
