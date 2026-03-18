"""Security for DAG execution"""

import hashlib
import hmac
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger("orchestration.security")


@dataclass
class TaskPermissions:
    """Permissions for task execution"""
    task_id: str
    allowed_agents: set
    read_only: bool = False


class TaskValidator:
    """Validate task security"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or "default-secret"
    
    def sign_task(self, task_id: str, data: Any) -> str:
        """Sign task data"""
        message = f"{task_id}:{str(data)}"
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
    
    def verify_task(self, task_id: str, data: Any, signature: str) -> bool:
        """Verify task signature"""
        expected = self.sign_task(task_id, data)
        return hmac.compare_digest(expected, signature)
    
    def validate_task(self, task: "Task") -> bool:
        """Validate task can be executed"""
        # Check for path traversal
        if hasattr(task, 'args'):
            for arg in task.args:
                if isinstance(arg, str) and ".." in arg:
                    logger.warning(f"Path traversal detected in {task.id}")
                    return False
        
        return True


class ResourceGuard:
    """Guard resource access"""
    
    def __init__(self, max_memory_mb: int = 1024, max_cpu_percent: int = 80):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
    
    def check_resources(self) -> bool:
        """Check if resources available"""
        # Placeholder - real implementation would check actual resources
        return True
    
    def estimate_memory(self, data_size: int) -> int:
        """Estimate memory usage"""
        return data_size * 2  # 2x for overhead
    
    def can_execute(self, estimated_memory_mb: int) -> bool:
        """Check if can execute with estimated memory"""
        return estimated_memory_mb <= self.max_memory_mb


class SecurityManager:
    """Manage security"""
    
    def __init__(self):
        self.validator = TaskValidator()
        self.guard = ResourceGuard()
        self.blocked_tasks: set = set()
    
    def is_allowed(self, task_id: str) -> bool:
        """Check if task is allowed"""
        return task_id not in self.blocked_tasks
    
    def block_task(self, task_id: str):
        """Block task"""
        self.blocked_tasks.add(task_id)
    
    def unblock_task(self, task_id: str):
        """Unblock task"""
        self.blocked_tasks.discard(task_id)
    
    def validate(self, task: "Task") -> Dict[str, Any]:
        """Validate task"""
        return {
            "allowed": self.is_allowed(task.id) and self.validator.validate_task(task),
            "resources": self.guard.check_resources(),
        }


# Global security manager
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get security manager"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager
