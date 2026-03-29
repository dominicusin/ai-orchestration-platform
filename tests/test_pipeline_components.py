"""Tests for pipeline components"""


from orchestration.config import ConfigManager, DAGConfig
from orchestration.context import ContextManager, PipelineContext
from orchestration.events import EventBus
from orchestration.state import State, StateManager, StateStatus


class TestDAGConfig:
    """Test DAGConfig"""

    def test_config_creation(self):
        """Test config creation"""
        c = DAGConfig()
        assert c is not None


class TestConfigManager:
    """Test ConfigManager"""

    def test_manager(self):
        """Test manager"""
        m = ConfigManager()
        assert m is not None


class TestPipelineContext:
    """Test PipelineContext"""

    def test_context_creation(self):
        """Test context creation"""
        ctx = PipelineContext()
        assert ctx is not None


class TestContextManager:
    """Test ContextManager"""

    def test_manager(self):
        """Test manager"""
        m = ContextManager()
        assert m is not None


class TestEventBus:
    """Test EventBus"""

    def test_event_bus(self):
        """Test event bus"""
        bus = EventBus()
        assert bus is not None


class TestExecutionState:
    """Test ExecutionState - using State"""

    def test_state_creation(self):
        """Test state creation"""
        state = State(name="test-123", status=StateStatus.ACTIVE)
        assert state.name == "test-123"
        assert state.is_active() is True


class TestStateManager:
    """Test StateManager"""

    def test_manager(self):
        """Test manager"""
        m = StateManager()
        assert m is not None
