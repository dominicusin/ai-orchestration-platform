"""Tests for State Management"""

import pytest

from orchestration.state import (
    StateStatus,
    StateTransition,
    State,
    StateMachine,
    StateStore,
    StateManager,
    get_state_manager,
)


class TestStateStatus:
    """Test StateStatus"""

    def test_values(self):
        """Test enum values"""
        assert StateStatus.PENDING.value == "pending"
        assert StateStatus.ACTIVE.value == "active"
        assert StateStatus.COMPLETED.value == "completed"
        assert StateStatus.FAILED.value == "failed"


class TestStateTransition:
    """Test StateTransition"""

    def test_creation(self):
        """Test creation"""
        transition = StateTransition(StateStatus.PENDING, StateStatus.ACTIVE)
        assert transition.from_state == StateStatus.PENDING
        assert transition.to_state == StateStatus.ACTIVE


class TestState:
    """Test State"""

    def test_creation(self):
        """Test creation"""
        state = State(name="test", status=StateStatus.PENDING)
        assert state.name == "test"
        assert state.status == StateStatus.PENDING

    def test_update(self):
        """Test update"""
        state = State(name="test")
        state.update(StateStatus.ACTIVE, "data", {"key": "value"})
        assert state.status == StateStatus.ACTIVE
        assert state.data == "data"
        assert state.metadata["key"] == "value"

    def test_is_active(self):
        """Test is_active"""
        state = State(name="test", status=StateStatus.ACTIVE)
        assert state.is_active() is True

    def test_is_completed(self):
        """Test is_completed"""
        state = State(name="test", status=StateStatus.COMPLETED)
        assert state.is_completed() is True

    def test_is_failed(self):
        """Test is_failed"""
        state = State(name="test", status=StateStatus.FAILED)
        assert state.is_failed() is True


class TestStateMachine:
    """Test StateMachine"""

    @pytest.fixture
    def machine(self):
        """Create machine"""
        m = StateMachine("test")
        m.add_state("s1", StateStatus.PENDING)
        m.add_state("s2", StateStatus.ACTIVE)
        m.add_transition(StateStatus.PENDING, StateStatus.ACTIVE)
        m.add_transition(StateStatus.ACTIVE, StateStatus.COMPLETED)
        return m

    def test_creation(self):
        """Test creation"""
        machine = StateMachine("test")
        assert machine.name == "test"

    def test_add_state(self, machine):
        """Test add state"""
        machine.add_state("s3", StateStatus.COMPLETED)
        assert machine.get_state("s3") is not None

    def test_can_transition(self, machine):
        """Test can transition"""
        assert machine.can_transition("s1", StateStatus.ACTIVE) is True
        assert machine.can_transition("s1", StateStatus.COMPLETED) is False

    def test_transition(self, machine):
        """Test transition"""
        result = machine.transition("s1", StateStatus.ACTIVE)
        assert result is True
        assert machine.get_state("s1").status == StateStatus.ACTIVE

    def test_get_states_by_status(self, machine):
        """Test get states by status"""
        machine.transition("s1", StateStatus.ACTIVE)
        states = machine.get_states_by_status(StateStatus.ACTIVE)
        assert len(states) >= 1


class TestStateStore:
    """Test StateStore"""

    @pytest.fixture
    def store(self):
        """Create store"""
        return StateStore()

    def test_creation(self, store):
        """Test creation"""
        assert store is not None

    def test_save_load(self, store):
        """Test save and load"""
        state = State(name="test", status=StateStatus.PENDING)
        store.save(state)
        loaded = store.load("test")
        assert loaded is not None
        assert loaded.name == "test"

    def test_delete(self, store):
        """Test delete"""
        state = State(name="test")
        store.save(state)
        assert store.delete("test") is True
        assert store.load("test") is None

    def test_list_names(self, store):
        """Test list names"""
        store.save(State(name="a"))
        store.save(State(name="b"))
        names = store.list_names()
        assert "a" in names
        assert "b" in names


class TestStateManager:
    """Test StateManager"""

    @pytest.fixture
    def manager(self):
        """Create manager"""
        return StateManager()

    def test_creation(self, manager):
        """Test creation"""
        assert manager is not None

    def test_create_machine(self, manager):
        """Test create machine"""
        machine = manager.create_machine("test")
        assert machine is not None
        assert manager.get_machine("test") is machine

    def test_create_store(self, manager):
        """Test create store"""
        store = manager.create_store("test")
        assert store is not None
        assert manager.get_store("test") is store


class TestGetStateManager:
    """Test singleton"""

    def test_singleton(self):
        """Test singleton"""
        m1 = get_state_manager()
        m2 = get_state_manager()
        assert m1 is m2
