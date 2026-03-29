"""Error definitions for DAG execution"""



class DAGError(Exception):
    """Base DAG error"""
    pass


class TaskNotFoundError(DAGError):
    """Task not found"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")


class CycleDetectedError(DAGError):
    """Cycle detected in DAG"""
    pass


class AgentNotAvailableError(DAGError):
    """No agent available"""
    def __init__(self, capability: str = None):
        self.capability = capability
        super().__init__("No agent available" + (f" with capability: {capability}" if capability else ""))


class TaskExecutionError(DAGError):
    """Task execution failed"""
    def __init__(self, task_id: str, error: str):
        self.task_id = task_id
        self.error = error
        super().__init__(f"Task {task_id} failed: {error}")


class ValidationError(DAGError):
    """Validation failed"""
    pass


class ResourceLimitError(DAGError):
    """Resource limit exceeded"""
    pass
