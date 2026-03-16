"""Error handling and custom exceptions"""

import traceback
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("orchestration.errors")


class ErrorCode(Enum):
    """Error codes"""
    # General errors
    UNKNOWN = "UNKNOWN"
    NOT_FOUND = "NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
    TIMEOUT = "TIMEOUT"
    
    # AI errors
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    AI_RATE_LIMIT = "AI_RATE_LIMIT"
    AI_AUTH_ERROR = "AI_AUTH_ERROR"
    AI_QUOTA_EXCEEDED = "AI_QUOTA_EXCEEDED"
    
    # File errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_READ_ERROR = "FILE_READ_ERROR"
    FILE_WRITE_ERROR = "FILE_WRITE_ERROR"
    
    # Pipeline errors
    PIPELINE_ERROR = "PIPELINE_ERROR"
    PHASE_ERROR = "PHASE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"


@dataclass
class ErrorDetail:
    """Error detail"""
    code: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class PipelineError(Exception):
    """Base pipeline error"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN,
        details: Dict[str, Any] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        
        super().__init__(message)
    
    def to_dict(self) -> Dict:
        return {
            "error": self.message,
            "code": self.code.value,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class ProviderError(PipelineError):
    """AI provider error"""
    def __init__(self, message: str, provider: str = None, **kwargs):
        super().__init__(message, ErrorCode.AI_PROVIDER_ERROR, **kwargs)
        self.provider = provider


class RateLimitError(PipelineError):
    """Rate limit error"""
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, ErrorCode.AI_RATE_LIMIT, **kwargs)
        self.retry_after = retry_after


class ValidationError(PipelineError):
    """Validation error"""
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, **kwargs)
        self.field = field


class FileError(PipelineError):
    """File operation error"""
    def __init__(self, message: str, path: str = None, **kwargs):
        super().__init__(message, ErrorCode.FILE_NOT_FOUND, **kwargs)
        self.path = path


class ErrorHandler:
    """Centralized error handling"""
    
    def __init__(self):
        self.errors: list = []
    
    def handle(self, error: Exception, context: Dict = None) -> Dict:
        """Handle error"""
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            "traceback": traceback.format_exc(),
        }
        
        if isinstance(error, PipelineError):
            error_info["code"] = error.code.value
            error_info["details"] = error.details
        
        self.errors.append(error_info)
        
        # Log error
        logger.error(f"Error: {error_info['message']}")
        
        return error_info
    
    def get_errors(self, limit: int = 100) -> list:
        """Get recent errors"""
        return self.errors[-limit:]
    
    def clear_errors(self):
        """Clear error history"""
        self.errors = []


# Global handler
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get error handler"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler
