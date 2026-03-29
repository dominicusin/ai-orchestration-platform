"""Tests for Registries"""

import pytest

from orchestration.registries import (
    Registry,
    RegistryEntry,
    TypeRegistry,
    HierarchicalRegistry,
    LazyRegistry,
    get_registry,
    register,
    get,
)


class TestRegistryEntry:
    """Test RegistryEntry"""

    def test_creation(self):
        """Test creation"""
        entry = RegistryEntry(name="test", obj="value", tags=["tag1"], metadata={"key": "val"})
        assert entry.name == "test"
        assert entry.obj == "value"
        assert entry.tags == ["tag1"]
        assert entry.metadata["key"] == "val"


class TestRegistry:
    """Test Registry"""

    @pytest.fixture
    def registry(self):
        """Create registry"""
        return Registry("test")

    def test_creation(self, registry):
        """Test creation"""
        assert registry.name == "test"
        assert registry.count() == 0

    def test_register(self, registry):
        """Test register"""
        registry.register("key", "value")
        assert registry.exists("key") is True

    def test_unregister(self, registry):
        """Test unregister"""
        registry.register("key", "value")
        assert registry.unregister("key") is True
        assert registry.exists("key") is False

    def test_get(self, registry):
        """Test get"""
        registry.register("key", "value")
        assert registry.get("key") == "value"
        assert registry.get("missing") is None

    def test_list_names(self, registry):
        """Test list names"""
        registry.register("a", 1)
        registry.register("b", 2)
        assert registry.list_names() == ["a", "b"]

    def test_list_objects(self, registry):
        """Test list objects"""
        registry.register("a", 1)
        registry.register("b", 2)
        assert registry.list_objects() == [1, 2]

    def test_find_by_tag(self, registry):
        """Test find by tag"""
        registry.register("a", 1, tags=["x"])
        registry.register("b", 2, tags=["y"])
        registry.register("c", 3, tags=["x"])

        results = registry.find_by_tag("x")
        assert len(results) == 2

    def test_find_by_metadata(self, registry):
        """Test find by metadata"""
        registry.register("a", 1, metadata={"type": "numeric"})
        registry.register("b", "text", metadata={"type": "text"})

        results = registry.find_by_metadata("type", "text")
        assert results == ["text"]

    def test_clear(self, registry):
        """Test clear"""
        registry.register("a", 1)
        registry.clear()
        assert registry.count() == 0


class TestTypeRegistry:
    """Test TypeRegistry"""

    @pytest.fixture
    def registry(self):
        """Create registry"""
        return TypeRegistry()

    def test_register_with_type(self, registry):
        """Test register with type"""
        registry.register("str", "hello", str)
        entry = registry.get_entry("str")
        assert entry.metadata["type"] == "str"

    def test_get_by_type(self, registry):
        """Test get by type"""
        registry.register("str", "hello", str)
        registry.register("num", 42, int)

        results = registry.get_by_type(str)
        assert results == ["hello"]


class TestHierarchicalRegistry:
    """Test HierarchicalRegistry"""

    def test_with_parent(self):
        """Test with parent"""
        parent = Registry("parent")
        parent.register("shared", "parent_value")

        child = HierarchicalRegistry("child", parent)
        child.register("local", "child_value")

        assert child.get("local") == "child_value"
        assert child.get("shared") == "parent_value"


class TestLazyRegistry:
    """Test LazyRegistry"""

    @pytest.fixture
    def registry(self):
        """Create registry"""
        return LazyRegistry()

    def test_register_factory(self, registry):
        """Test register factory"""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return "created"

        registry.register_factory("lazy", factory)
        assert registry.count() == 1
        assert call_count == 0

        # First access creates the object
        result = registry.get("lazy")
        assert result == "created"
        assert call_count == 1

        # Second access returns cached
        result = registry.get("lazy")
        assert call_count == 1


class TestGlobalRegistry:
    """Test global registry functions"""

    def test_register_and_get(self):
        """Test register and get"""
        register("test_key", "test_value")
        assert get("test_key") == "test_value"

        # Clean up
        get_registry().clear()
