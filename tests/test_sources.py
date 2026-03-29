"""Tests for Sources"""

import json
import os
import tempfile

import pytest

from orchestration.sources import (
    CallbackSource,
    DictSource,
    FileSource,
    GeneratorSource,
    JSONFileSource,
    ListSource,
    MultiSource,
    StringSource,
    create_file_source,
    create_json_source,
    create_multi_source,
    get_source,
)


class TestFileSource:
    """Test FileSource"""

    def test_read(self):
        """Test read"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            with open(path, "w") as f:
                f.write("test content")

            source = FileSource(path)
            content = source.read()
            assert content == "test content"
            source.close()

    def test_read_lines(self):
        """Test read lines"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            with open(path, "w") as f:
                f.write("line1\nline2\nline3\n")

            source = FileSource(path)
            lines = list(source.read_lines())
            assert lines == ["line1", "line2", "line3"]
            source.close()


class TestJSONFileSource:
    """Test JSONFileSource"""

    def test_read_dict(self):
        """Test read dict"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            with open(path, "w") as f:
                json.dump({"key": "value"}, f)

            source = JSONFileSource(path)
            data = source.read()
            assert data == {"key": "value"}

    def test_read_list(self):
        """Test read list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            with open(path, "w") as f:
                f.write('{"key": "value1"}\n{"key": "value2"}\n')

            source = JSONFileSource(path, lines=True)
            data = source.read()
            assert len(data) == 2


class TestStringSource:
    """Test StringSource"""

    def test_read(self):
        """Test read"""
        source = StringSource("test string")
        assert source.read() == "test string"


class TestListSource:
    """Test ListSource"""

    def test_read(self):
        """Test read"""
        source = ListSource([1, 2, 3])
        assert source.read() == [1, 2, 3]


class TestDictSource:
    """Test DictSource"""

    def test_read(self):
        """Test read"""
        source = DictSource({"key": "value"})
        assert source.read() == {"key": "value"}


class TestGeneratorSource:
    """Test GeneratorSource"""

    def test_read(self):
        """Test read"""
        gen = (x for x in [1, 2, 3])
        source = GeneratorSource(gen)
        assert source.read() == 1
        assert source.read() == 2
        assert source.read() == 3
        assert source.read() is None

    def test_read_all(self):
        """Test read all"""
        gen = (x for x in [1, 2, 3])
        source = GeneratorSource(gen)
        assert source.read_all() == [1, 2, 3]


class TestCallbackSource:
    """Test CallbackSource"""

    def test_callback(self):
        """Test callback"""
        source = CallbackSource(lambda: "callback result")
        assert source.read() == "callback result"


class TestMultiSource:
    """Test MultiSource"""

    def test_read_multiple(self):
        """Test read multiple"""
        sources = [
            StringSource("a"),
            StringSource("b"),
            StringSource("c"),
        ]
        multi = MultiSource(*sources)

        assert multi.read() == "a"
        assert multi.read() == "b"
        assert multi.read() == "c"
        assert multi.read() is None

    def test_read_all(self):
        """Test read all"""
        sources = [
            StringSource("a"),
            StringSource("b"),
        ]
        multi = MultiSource(*sources)
        results = multi.read_all()
        assert results == ["a", "b"]

    def test_reset(self):
        """Test reset"""
        sources = [StringSource("a"), StringSource("b")]
        multi = MultiSource(*sources)

        multi.read()
        multi.reset()
        assert multi.read() == "a"


class TestFactoryFunctions:
    """Test factory functions"""

    def test_get_source_string(self):
        """Test get source string"""
        source = get_source("string", data="test")
        assert isinstance(source, StringSource)

    def test_get_source_list(self):
        """Test get source list"""
        source = get_source("list", data=[1, 2, 3])
        assert isinstance(source, ListSource)

    def test_get_source_dict(self):
        """Test get source dict"""
        source = get_source("dict", data={"key": "value"})
        assert isinstance(source, DictSource)

    def test_get_source_unknown(self):
        """Test unknown source"""
        with pytest.raises(ValueError):
            get_source("unknown")

    def test_create_file_source(self):
        """Test create file source"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            source = create_file_source(path)
            assert isinstance(source, FileSource)

    def test_create_json_source(self):
        """Test create json source"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            source = create_json_source(path)
            assert isinstance(source, JSONFileSource)

    def test_create_multi_source(self):
        """Test create multi source"""
        source = create_multi_source(StringSource("a"), StringSource("b"))
        assert isinstance(source, MultiSource)
