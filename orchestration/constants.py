"""Constants for DAG execution"""

from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(StrEnum):
    ATOMIC = "atomic"
    COMPOSITE = "composite"
    PIPELINE = "pipeline"


class AgentCapability(StrEnum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    LLM_CALL = "llm_call"
    CODE_EXECUTE = "code_execute"
    DATA_TRANSFORM = "data_transform"
    VALIDATE = "validate"
    FORMAT = "format"


# Default values
DEFAULT_MAX_WORKERS = 4
DEFAULT_TIMEOUT = 300
DEFAULT_MAX_RETRIES = 3
DEFAULT_CHUNK_SIZE = 100

# Limits
MAX_DEPTH = 10
MAX_TASKS = 10000
MAX_CONCURRENT_LAYERS = 100
