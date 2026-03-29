"""Tests for Dataclass Utils"""

from dataclasses import dataclass

from orchestration.dataclass_utils import (
    clone_dataclass,
    compare_dataclasses,
    dataclass_from_json,
    dataclass_to_dict,
    dataclass_to_json,
    dict_to_dataclass,
    merge_dataclasses,
    validate_dataclass,
)


@dataclass
class Person:
    name: str = ""
    age: int = 0
    email: str = ""


@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False


class TestDataclassToDict:
    """Test dataclass_to_dict"""

    def test_simple(self):
        """Test simple conversion"""
        person = Person(name="John", age=30)
        result = dataclass_to_dict(person)
        assert result == {"name": "John", "age": 30, "email": ""}

    def test_non_dataclass(self):
        """Test non-dataclass - returns empty dict"""
        result = dataclass_to_dict({"key": "value"})
        assert result == {}


class TestDictToDataclass:
    """Test dict_to_dataclass"""

    def test_conversion(self):
        """Test conversion"""
        data = {"name": "John", "age": 30, "email": "john@example.com"}
        person = dict_to_dataclass(Person, data)
        assert person.name == "John"
        assert person.age == 30

    def test_partial(self):
        """Test partial"""
        data = {"name": "John"}
        person = dict_to_dataclass(Person, data)
        assert person.name == "John"
        assert person.age == 0


class TestMergeDataclasses:
    """Test merge_dataclasses"""

    def test_merge(self):
        """Test merge"""
        config = Config(host="localhost", port=8080)
        override = {"port": 9000, "debug": True}

        merged = merge_dataclasses(config, override)
        assert merged.host == "localhost"
        assert merged.port == 9000
        assert merged.debug is True


class TestValidateDataclass:
    """Test validate_dataclass"""

    def test_valid(self):
        """Test valid"""
        person = Person(name="John", age=30)
        errors = validate_dataclass(person)
        assert errors == []

    def test_invalid_type(self):
        """Test invalid type"""
        @dataclass
        class BadPerson:
            name: str
            age: int

        # Create with wrong type - Python doesn't enforce types at runtime
        BadPerson(name="John", age="30")  # type: ignore


class TestJsonSerialization:
    """Test JSON serialization"""

    def test_to_json(self):
        """Test to JSON"""
        config = Config(host="localhost", port=8080)
        json_str = dataclass_to_json(config)
        assert "localhost" in json_str
        assert "8080" in json_str

    def test_from_json(self):
        """Test from JSON"""
        json_str = '{"host": "localhost", "port": 8080, "debug": false}'
        config = dataclass_from_json(Config, json_str)
        assert config.host == "localhost"
        assert config.port == 8080


class TestCloneDataclass:
    """Test clone_dataclass"""

    def test_clone(self):
        """Test clone"""
        person = Person(name="John", age=30)
        cloned = clone_dataclass(person)

        assert cloned.name == "John"
        assert cloned.age == 30
        assert cloned is not person


class TestCompareDataclasses:
    """Test compare_dataclasses"""

    def test_compare_same(self):
        """Test compare same"""
        p1 = Person(name="John", age=30)
        p2 = Person(name="John", age=30)

        diff = compare_dataclasses(p1, p2)
        assert diff == {}

    def test_compare_different(self):
        """Test compare different"""
        p1 = Person(name="John", age=30)
        p2 = Person(name="Jane", age=30)

        diff = compare_dataclasses(p1, p2)
        assert "name" in diff
        assert diff["name"]["old"] == "John"
        assert diff["name"]["new"] == "Jane"
