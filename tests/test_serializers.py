"""Tests for Serializers"""

from dataclasses import dataclass

import pytest

from orchestration.serializers import (
    JSONSerializer,
    PickleSerializer,
    XMLSerializer,
    deserialize,
    from_json,
    from_pickle,
    from_xml,
    get_serializer,
    serialize,
    to_json,
    to_pickle,
    to_xml,
)


@dataclass
class TestData:
    name: str
    value: int


class TestJSONSerializer:
    """Test JSONSerializer"""

    @pytest.fixture
    def serializer(self):
        """Create serializer"""
        return JSONSerializer()

    def test_serialize_dict(self, serializer):
        """Test serialize dict"""
        data = {"key": "value", "num": 42}
        result = serializer.serialize(data)
        assert "key" in result
        assert "value" in result

    def test_serialize_dataclass(self, serializer):
        """Test serialize dataclass"""
        data = TestData(name="test", value=42)
        result = serializer.serialize(data)
        assert "test" in result
        assert "42" in result

    def test_deserialize(self, serializer):
        """Test deserialize"""
        data = '{"key": "value"}'
        result = serializer.deserialize(data)
        assert result["key"] == "value"


class TestPickleSerializer:
    """Test PickleSerializer"""

    @pytest.fixture
    def serializer(self):
        """Create serializer"""
        return PickleSerializer()

    def test_serialize_deserialize(self, serializer):
        """Test serialize/deserialize"""
        data = {"key": "value", "list": [1, 2, 3]}
        serialized = serializer.serialize(data)
        result = serializer.deserialize(serialized)
        assert result == data

    def test_serialize_complex(self, serializer):
        """Test serialize complex objects"""
        data = {"nested": {"inner": [1, 2, 3]}}
        serialized = serializer.serialize(data)
        result = serializer.deserialize(serialized)
        assert result == data


class TestXMLSerializer:
    """Test XMLSerializer"""

    @pytest.fixture
    def serializer(self):
        """Create serializer"""
        return XMLSerializer()

    def test_serialize_dict(self, serializer):
        """Test serialize dict"""
        data = {"key": "value"}
        result = serializer.serialize(data)
        assert "<key>value</key>" in result

    def test_serialize_nested(self, serializer):
        """Test serialize nested"""
        data = {"outer": {"inner": "value"}}
        result = serializer.serialize(data)
        assert "outer" in result
        assert "inner" in result

    def test_deserialize(self, serializer):
        """Test deserialize"""
        xml = "<root><key>value</key></root>"
        result = serializer.deserialize(xml)
        assert result["key"] == "value"


class TestFactoryFunctions:
    """Test factory functions"""

    def test_get_serializer_json(self):
        """Test get serializer json"""
        s = get_serializer("json")
        assert isinstance(s, JSONSerializer)

    def test_get_serializer_pickle(self):
        """Test get serializer pickle"""
        s = get_serializer("pickle")
        assert isinstance(s, PickleSerializer)

    def test_get_serializer_xml(self):
        """Test get serializer xml"""
        s = get_serializer("xml")
        assert isinstance(s, XMLSerializer)

    def test_get_serializer_unknown(self):
        """Test unknown serializer"""
        with pytest.raises(ValueError):
            get_serializer("unknown")

    def test_serialize_json(self):
        """Test serialize"""
        result = serialize({"key": "value"}, "json")
        assert "key" in result

    def test_deserialize_json(self):
        """Test deserialize"""
        result = deserialize('{"key": "value"}', "json")
        assert result["key"] == "value"


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_to_json(self):
        """Test to_json"""
        result = to_json({"key": "value"})
        assert "key" in result

    def test_from_json(self):
        """Test from_json"""
        result = from_json('{"key": "value"}')
        assert result["key"] == "value"

    def test_to_pickle(self):
        """Test to_pickle"""
        result = to_pickle({"key": "value"})
        assert isinstance(result, str)

    def test_from_pickle(self):
        """Test from_pickle"""
        pickled = to_pickle({"key": "value"})
        result = from_pickle(pickled)
        assert result["key"] == "value"

    def test_to_xml(self):
        """Test to_xml"""
        result = to_xml({"key": "value"})
        assert "<key>value</key>" in result

    def test_from_xml(self):
        """Test from_xml"""
        result = from_xml("<root><key>value</key></root>")
        assert result["key"] == "value"
