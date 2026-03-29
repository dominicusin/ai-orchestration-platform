"""Tests for Results"""

import pytest

from orchestration.results import (
    Result,
    ResultBuilder,
    ResultCollection,
    ResultStatus,
    failure,
    partial,
    success,
)


class TestResultStatus:
    """Test ResultStatus"""

    def test_values(self):
        """Test enum values"""
        assert ResultStatus.SUCCESS.value == "success"
        assert ResultStatus.FAILURE.value == "failure"
        assert ResultStatus.PARTIAL.value == "partial"
        assert ResultStatus.PENDING.value == "pending"
        assert ResultStatus.CANCELLED.value == "cancelled"


class TestResult:
    """Test Result"""

    def test_creation(self):
        """Test creation"""
        result = Result(status=ResultStatus.SUCCESS, data="test")
        assert result.status == ResultStatus.SUCCESS
        assert result.data == "test"

    def test_is_success(self):
        """Test is_success"""
        result = Result(status=ResultStatus.SUCCESS)
        assert result.is_success() is True
        assert result.is_failure() is False

    def test_is_failure(self):
        """Test is_failure"""
        result = Result(status=ResultStatus.FAILURE, error="error")
        assert result.is_failure() is True
        assert result.is_success() is False

    def test_is_pending(self):
        """Test is_pending"""
        result = Result(status=ResultStatus.PENDING)
        assert result.is_pending() is True

    def test_get_data(self):
        """Test get_data"""
        result = Result(status=ResultStatus.SUCCESS, data="value")
        assert result.get_data() == "value"
        assert result.get_data(default="default") == "value"

    def test_get_data_default(self):
        """Test get_data with default"""
        result = Result(status=ResultStatus.SUCCESS, data=None)
        assert result.get_data(default="default") == "default"


class TestResultBuilder:
    """Test ResultBuilder"""

    @pytest.fixture
    def builder(self):
        """Create builder"""
        return ResultBuilder()

    def test_success(self, builder):
        """Test success"""
        result = builder.success(data="data", message="ok")
        assert result.is_success() is True
        assert result.data == "data"

    def test_failure(self, builder):
        """Test failure"""
        result = builder.failure(error="error", message="fail")
        assert result.is_failure() is True
        assert result.error == "error"

    def test_partial(self, builder):
        """Test partial"""
        result = builder.partial(data="partial")
        assert result.status == ResultStatus.PARTIAL

    def test_pending(self, builder):
        """Test pending"""
        result = builder.pending(message="waiting")
        assert result.is_pending() is True

    def test_cancelled(self, builder):
        """Test cancelled"""
        result = builder.cancelled(message="cancelled")
        assert result.status == ResultStatus.CANCELLED

    def test_with_metadata(self, builder):
        """Test with metadata"""
        result = builder.with_metadata("key", "value").success()
        assert result.metadata["key"] == "value"


class TestHelperFunctions:
    """Test helper functions"""

    def test_success_function(self):
        """Test success function"""
        result = success(data="ok", message="done")
        assert result.is_success() is True

    def test_failure_function(self):
        """Test failure function"""
        result = failure(error="error")
        assert result.is_failure() is True

    def test_partial_function(self):
        """Test partial function"""
        result = partial(data="partial")
        assert result.status == ResultStatus.PARTIAL


class TestResultCollection:
    """Test ResultCollection"""

    @pytest.fixture
    def collection(self):
        """Create collection"""
        return ResultCollection()

    def test_creation(self, collection):
        """Test creation"""
        assert collection.count() == 0

    def test_add(self, collection):
        """Test add"""
        collection.add(success())
        collection.add(failure("error"))
        assert collection.count() == 2

    def test_get_successful(self, collection):
        """Test get successful"""
        collection.add(success())
        collection.add(failure("error"))
        collection.add(success())
        assert collection.successful_count() == 2

    def test_get_failed(self, collection):
        """Test get failed"""
        collection.add(success())
        collection.add(failure("error"))
        assert collection.failed_count() == 1

    def test_is_all_success(self, collection):
        """Test is_all_success"""
        collection.add(success())
        collection.add(success())
        assert collection.is_all_success() is True

    def test_is_any_failure(self, collection):
        """Test is_any_failure"""
        collection.add(success())
        collection.add(failure("error"))
        assert collection.is_any_failure() is True
