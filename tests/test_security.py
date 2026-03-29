"""Tests for security module"""

from orchestration.security import SecurityManager, TaskPermissions, TaskValidator


class TestTaskValidator:
    """Test TaskValidator"""

    def test_validator_creation(self):
        """Test creation"""
        validator = TaskValidator(secret_key="test")
        assert validator is not None

    def test_sign_task(self):
        """Test sign task"""
        validator = TaskValidator(secret_key="test")
        sig = validator.sign_task("task1", {"data": "value"})
        assert sig is not None
        assert len(sig) > 0

    def test_verify_task(self):
        """Test verify task"""
        validator = TaskValidator(secret_key="test")
        data = {"data": "value"}
        sig = validator.sign_task("task1", data)
        assert validator.verify_task("task1", data, sig) is True


class TestTaskPermissions:
    """Test TaskPermissions"""

    def test_permissions_creation(self):
        """Test creation"""
        perm = TaskPermissions(task_id="test", allowed_agents={"agent1"})
        assert perm.task_id == "test"


class TestSecurityManager:
    """Test SecurityManager"""

    def test_manager(self):
        """Test manager"""
        m = SecurityManager()
        assert m is not None
