"""Tests for Errors"""

import pytest

from orchestration.errors import (
    OrchestrationError,
    PipelineError,
    StageError,
    ValidationError,
    ConfigurationError,
    ResourceError,
    TimeoutError,
    RetryExhaustedError,
    CircuitBreakerError,
    RateLimitError,
    ErrorContext,
    ErrorHandler,
    ErrorRecovery,
    safe_execute,
    get_error_handler,
)


class TestOrchestrationError:
    """Test OrchestrationError"""

    def test_creation(self):
        """Test creation"""
        err = OrchestrationError("test error", {"key": "value"})
        assert err.message == "test error"
        assert err.details["key"] == "value"


class TestStageError:
    """Test StageError"""

    def test_creation_with_stage(self):
        """Test creation with stage name"""
        err = StageError("stage failed", stage_name="transform")
        assert err.stage_name == "transform"


class TestRetryExhaustedError:
    """Test RetryExhaustedError"""

    def test_creation(self):
        """Test creation"""
        err = RetryExhaustedError("retry failed", attempts=3, last_error=ValueError("test"))
        assert err.attempts == 3
        assert isinstance(err.last_error, ValueError)


class TestRateLimitError:
    """Test RateLimitError"""

    def test_creation_with_retry_after(self):
        """Test creation with retry_after"""
        err = RateLimitError("rate limited", retry_after=60.0)
        assert err.retry_after == 60.0


class TestErrorContext:
    """Test ErrorContext"""

    def test_creation(self):
        """Test creation"""
        ctx = ErrorContext(error_type="ValueError", message="test error")
        assert ctx.error_type == "ValueError"
        assert ctx.message == "test error"
        assert ctx.timestamp is not None


class TestErrorHandler:
    """Test ErrorHandler"""

    @pytest.fixture
    def handler(self):
        """Create handler"""
        return ErrorHandler()

    def test_creation(self, handler):
        """Test creation"""
        assert handler is not None

    def test_register_handler(self, handler):
        """Test register handler"""
        def custom_handler(e, ctx):
            return "handled"

        handler.register_handler(ValueError, custom_handler)
        assert ValueError in handler._handlers

    def test_handle(self, handler):
        """Test handle"""
        handler.handle(ValueError("test error"), reraise=False)
        log = handler.get_error_log()
        assert len(log) == 1
        assert log[0].error_type == "ValueError"

    def test_get_errors_by_type(self, handler):
        """Test get errors by type"""
        handler.handle(ValueError("test1"), reraise=False)
        handler.handle(TypeError("test2"), reraise=False)
        handler.handle(ValueError("test3"), reraise=False)

        errors = handler.get_errors_by_type("ValueError")
        assert len(errors) == 2

    def test_clear_log(self, handler):
        """Test clear log"""
        handler.handle(ValueError("test"), reraise=False)
        handler.clear_log()
        assert len(handler.get_error_log()) == 0


class TestErrorRecovery:
    """Test ErrorRecovery"""

    def test_with_fallback(self):
        """Test with fallback"""
        def primary():
            raise ValueError("fail")

        def fallback():
            return "fallback"

        result = ErrorRecovery.with_fallback(fallback, primary)
        assert result == "fallback"

    def test_with_fallback_primary_success(self):
        """Test with fallback when primary succeeds"""
        def primary():
            return "success"

        def fallback():
            return "fallback"

        result = ErrorRecovery.with_fallback(fallback, primary)
        assert result == "success"

    def test_with_retry_success(self):
        """Test with retry success"""
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "success"

        result = ErrorRecovery.with_retry(func, max_attempts=3, delay=0.01)
        assert result == "success"
        assert call_count == 2

    def test_with_retry_exhausted(self):
        """Test with retry exhausted"""
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        with pytest.raises(ValueError):
            ErrorRecovery.with_retry(func, max_attempts=3, delay=0.01)

        assert call_count == 3


class TestSafeExecute:
    """Test safe_execute"""

    def test_success(self):
        """Test success"""
        result = safe_execute(lambda x: x * 2, default=0, x=5)
        assert result == 10

    def test_exception(self):
        """Test exception returns default"""
        result = safe_execute(lambda x: 1/0, default=0)
        assert result == 0


class TestGetErrorHandler:
    """Test singleton"""

    def test_singleton(self):
        """Test singleton"""
        h1 = get_error_handler()
        h2 = get_error_handler()
        assert h1 is h2
