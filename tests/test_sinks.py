"""Tests for Sinks"""

import os
import tempfile

import pytest

from orchestration.sinks import (
    CallbackSink,
    ConsoleSink,
    FileSink,
    JSONFileSink,
    ListSink,
    MultiSink,
    NullSink,
    create_console_sink,
    create_file_sink,
    create_multi_sink,
    get_sink,
)


class TestFileSink:
    """Test FileSink"""

    def test_write_text(self):
        """Test write text"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            with FileSink(path) as sink:
                sink.write("line 1")
                sink.write("line 2")

            with open(path) as f:
                content = f.read()
            assert "line 1" in content
            assert "line 2" in content

    def test_write_dict(self):
        """Test write dict"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            with FileSink(path) as sink:
                sink.write({"key": "value"})

            with open(path) as f:
                content = f.read()
            assert "key" in content


class TestJSONFileSink:
    """Test JSONFileSink"""

    def test_write_json(self):
        """Test write JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            with JSONFileSink(path) as sink:
                sink.write({"key": "value"})

            with open(path) as f:
                content = f.read()
            assert '"key"' in content


class TestConsoleSink:
    """Test ConsoleSink"""

    def test_write(self):
        """Test write - just ensure no error"""
        sink = ConsoleSink()
        sink.write("test")
        sink.write({"key": "value"})

    def test_format_json(self):
        """Test format json"""
        sink = ConsoleSink(format_json=True)
        sink.write({"key": "value"})


class TestListSink:
    """Test ListSink"""

    def test_write(self):
        """Test write"""
        sink = ListSink()
        sink.write("item1")
        sink.write("item2")
        assert len(sink.data) == 2

    def test_clear(self):
        """Test clear"""
        sink = ListSink()
        sink.write("item")
        sink.clear()
        assert len(sink.data) == 0

    def test_get_all(self):
        """Test get all"""
        sink = ListSink()
        sink.write("item1")
        sink.write("item2")
        assert sink.get_all() == ["item1", "item2"]


class TestNullSink:
    """Test NullSink"""

    def test_write(self):
        """Test write - no error"""
        sink = NullSink()
        sink.write("anything")
        sink.write({"key": "value"})


class TestCallbackSink:
    """Test CallbackSink"""

    def test_callback(self):
        """Test callback"""
        results = []

        def callback(data):
            results.append(data)

        sink = CallbackSink(callback)
        sink.write("test")
        sink.write({"key": "value"})

        assert results == ["test", {"key": "value"}]


class TestMultiSink:
    """Test MultiSink"""

    def test_multiple_sinks(self):
        """Test multiple sinks"""
        list_sink1 = ListSink()
        list_sink2 = ListSink()

        multi = MultiSink(list_sink1, list_sink2)
        multi.write("test")

        assert list_sink1.data == ["test"]
        assert list_sink2.data == ["test"]

    def test_add_sink(self):
        """Test add sink"""
        multi = MultiSink()
        list_sink = ListSink()

        multi.add_sink(list_sink)
        multi.write("test")

        assert list_sink.data == ["test"]


class TestFactoryFunctions:
    """Test factory functions"""

    def test_get_sink_console(self):
        """Test get sink console"""
        sink = get_sink("console")
        assert isinstance(sink, ConsoleSink)

    def test_get_sink_list(self):
        """Test get sink list"""
        sink = get_sink("list")
        assert isinstance(sink, ListSink)

    def test_get_sink_unknown(self):
        """Test unknown sink"""
        with pytest.raises(ValueError):
            get_sink("unknown")

    def test_create_file_sink(self):
        """Test create file sink"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            sink = create_file_sink(path)
            assert isinstance(sink, FileSink)

    def test_create_console_sink(self):
        """Test create console sink"""
        sink = create_console_sink()
        assert isinstance(sink, ConsoleSink)

    def test_create_multi_sink(self):
        """Test create multi sink"""
        sink = create_multi_sink(ListSink(), ListSink())
        assert isinstance(sink, MultiSink)
