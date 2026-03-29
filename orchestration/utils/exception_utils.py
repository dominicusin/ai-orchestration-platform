"""Exception utilities"""

import traceback


class BaseError(Exception):
    """Base error class"""
    code = "ERROR"

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(BaseError):
    """Validation error"""
    code = "VALIDATION_ERROR"


class NotFoundError(BaseError):
    """Not found error"""
    code = "NOT_FOUND"


class AuthenticationError(BaseError):
    """Authentication error"""
    code = "AUTH_ERROR"


class AuthorizationError(BaseError):
    """Authorization error"""
    code = "AUTHZ_ERROR"


def get_traceback(exc: Exception) -> str:
    """Get exception traceback"""
    return traceback.format_exc()


def reraise(exc: Exception, message: str):
    """Reraise with new message"""
    raise type(exc)(message) from exc
