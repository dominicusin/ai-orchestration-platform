"""Tests for Execution Context"""

import time

import pytest

from orchestration.execution_context import (
    ContextManager,
    ExecutionContext,
    add_context_tag,
    context,
    get_context_value,
    get_request_id,
    get_user_id,
    set_context_value,
    set_request_id,
    set_user_id,
)


class TestExecutionContext:
    """Test ExecutionContext"""

    def test_creation(self):
        """Test creation"""
        ctx = ExecutionContext()
        assert ctx.request_id == ""
        assert ctx.metadata == {}

    def test_get_set(self):
        """Test get/set"""
        ctx = ExecutionContext()
        ctx.set("key", "value")
        assert ctx.get("key") == "value"
        assert ctx.get("missing", "default") == "default"

    def test_add_tag(self):
        """Test add tag"""
        ctx = ExecutionContext()
        ctx.add_tag("tag1")
        ctx.add_tag("tag1")  # Duplicate
        assert "tag1" in ctx.tags
        assert len(ctx.tags) == 1

    def test_duration(self):
        """Test duration"""
        ctx = ExecutionContext()
        time.sleep(0.01)
        duration = ctx.duration()
        assert duration >= 0.01


class TestContextManager:
    """Test ContextManager"""

    @pytest.fixture
    def manager(self):
        """Create manager"""
        m = ContextManager()
        m.clear()
        return m

    def test_get_context(self, manager):
        """Test get context"""
        ctx = manager.get_context()
        assert isinstance(ctx, ExecutionContext)

    def test_set_context(self, manager):
        """Test set context"""
        new_ctx = ExecutionContext(request_id="test-123")
        manager.set_context(new_ctx)
        ctx = manager.get_context()
        assert ctx.request_id == "test-123"

    def test_clear(self, manager):
        """Test clear"""
        manager.get_context().set("key", "value")
        manager.clear()
        ctx = manager.get_context()
        assert ctx.metadata == {}

    def test_create_child(self, manager):
        """Test create child"""
        parent = manager.get_context()
        parent.request_id = "parent-id"
        parent.set("parent_key", "parent_value")

        child = manager.create_child(request_id="child-id", user_id="user-1")

        assert child.request_id == "child-id"
        assert child.user_id == "user-1"
        assert child.get("parent_key") == "parent_value"


class TestConvenienceFunctions:
    """Test convenience functions"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup"""
        ContextManager().clear()
        yield
        ContextManager().clear()

    def test_get_set_request_id(self):
        """Test request id"""
        set_request_id("req-123")
        assert get_request_id() == "req-123"

    def test_get_set_user_id(self):
        """Test user id"""
        set_user_id("user-456")
        assert get_user_id() == "user-456"

    def test_context_value(self):
        """Test context value"""
        set_context_value("key1", "value1")
        assert get_context_value("key1") == "value1"
        assert get_context_value("missing", "default") == "default"

    def test_add_tag(self):
        """Test add tag"""
        add_context_tag("test-tag")
        ctx = ContextManager().get_context()
        assert "test-tag" in ctx.tags


class TestContextManager2:
    """Test context manager"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup"""
        ContextManager().clear()
        yield
        ContextManager().clear()

    def test_context_function(self):
        """Test context function"""
        ctx = context(request_id="new-req", user_id="new-user")
        assert ctx.request_id == "new-req"
        assert ctx.user_id == "new-user"

        # After context, should be set
        parent = ContextManager().get_context()
        assert parent.request_id == "new-req"
