"""Tests for Stacks"""

import pytest

from orchestration.stacks import (
    MaxStack,
    MinStack,
    Stack,
    StackWithHistory,
    create_max_stack,
    create_min_stack,
    create_stack,
    create_stack_with_history,
)


class TestStack:
    """Test Stack"""

    @pytest.fixture
    def stack(self):
        """Create stack"""
        return Stack()

    def test_creation(self, stack):
        """Test creation"""
        assert stack.is_empty() is True

    def test_push_pop(self, stack):
        """Test push and pop"""
        stack.push(1)
        stack.push(2)
        assert stack.pop() == 2
        assert stack.pop() == 1

    def test_peek(self, stack):
        """Test peek"""
        stack.push(1)
        stack.push(2)
        assert stack.peek() == 2
        assert stack.size() == 2

    def test_pop_empty(self, stack):
        """Test pop from empty"""
        with pytest.raises(IndexError):
            stack.pop()

    def test_peek_empty(self, stack):
        """Test peek from empty"""
        with pytest.raises(IndexError):
            stack.peek()

    def test_size(self, stack):
        """Test size"""
        stack.push(1)
        stack.push(2)
        assert stack.size() == 2

    def test_clear(self, stack):
        """Test clear"""
        stack.push(1)
        stack.clear()
        assert stack.is_empty() is True

    def test_to_list(self, stack):
        """Test to_list"""
        stack.push(1)
        stack.push(2)
        assert stack.to_list() == [1, 2]


class TestMinStack:
    """Test MinStack"""

    @pytest.fixture
    def stack(self):
        """Create stack"""
        return MinStack()

    def test_get_min(self, stack):
        """Test get_min"""
        stack.push(3)
        stack.push(1)
        stack.push(4)
        assert stack.get_min() == 1

    def test_get_min_after_pop(self, stack):
        """Test get_min after pop"""
        stack.push(3)
        stack.push(1)
        stack.push(4)
        stack.pop()
        assert stack.get_min() == 1


class TestMaxStack:
    """Test MaxStack"""

    @pytest.fixture
    def stack(self):
        """Create stack"""
        return MaxStack()

    def test_get_max(self, stack):
        """Test get_max"""
        stack.push(3)
        stack.push(1)
        stack.push(4)
        assert stack.get_max() == 4


class TestStackWithHistory:
    """Test StackWithHistory"""

    @pytest.fixture
    def stack(self):
        """Create stack"""
        return StackWithHistory()

    def test_push_records_history(self, stack):
        """Test push records history"""
        stack.push(1)
        stack.push(2)
        history = stack.get_history()
        assert len(history) == 2
        assert history[0] == ("push", 1)
        assert history[1] == ("push", 2)

    def test_pop_records_history(self, stack):
        """Test pop records history"""
        stack.push(1)
        stack.push(2)
        stack.pop()
        history = stack.get_history()
        assert ("pop", 2) in history


class TestFactoryFunctions:
    """Test factory functions"""

    def test_create_stack(self):
        """Test create_stack"""
        s = create_stack()
        assert isinstance(s, Stack)

    def test_create_min_stack(self):
        """Test create_min_stack"""
        s = create_min_stack()
        assert isinstance(s, MinStack)

    def test_create_max_stack(self):
        """Test create_max_stack"""
        s = create_max_stack()
        assert isinstance(s, MaxStack)

    def test_create_stack_with_history(self):
        """Test create_stack_with_history"""
        s = create_stack_with_history()
        assert isinstance(s, StackWithHistory)
