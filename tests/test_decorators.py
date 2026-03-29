"""Tests for Decorators"""

import pytest
import time
import asyncio

from orchestration.decorators import (
    retry,
    async_retry,
    timing,
    async_timing,
    cache,
    log_calls,
    deprecated,
    once,
    rate_limit,
    validate_args,
    memoize,
    synchronized,
)


class TestRetry:
    """Test retry decorator"""

    def test_success_first_try(self):
        """Test success on first try"""
        call_count = 0

        @retry(max_attempts=3, delay=0.1)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = succeed()
        assert result == "success"
        assert call_count == 1

    def test_success_after_retries(self):
        """Test success after retries"""
        call_count = 0

        @retry(max_attempts=3, delay=0.1)
        def eventually_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("not yet")
            return "success"

        result = eventually_succeed()
        assert result == "success"
        assert call_count == 2

    def test_failure_after_max_attempts(self):
        """Test failure after max attempts"""
        call_count = 0

        @retry(max_attempts=3, delay=0.1)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fails")

        with pytest.raises(ValueError):
            always_fail()

        assert call_count == 3


class TestTiming:
    """Test timing decorator"""

    def test_timing(self):
        """Test timing decorator"""
        @timing
        def slow_func():
            time.sleep(0.05)
            return "done"

        result = slow_func()
        assert result == "done"


class TestCache:
    """Test cache decorator"""

    def test_cache(self):
        """Test cache decorator"""
        call_count = 0

        @cache(ttl=1.0)
        def cached_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert cached_func(5) == 10
        assert call_count == 1
        assert cached_func(5) == 10
        assert call_count == 1


class TestDeprecated:
    """Test deprecated decorator"""

    def test_deprecated(self):
        """Test deprecated decorator - just verify function works"""
        @deprecated("Use new_func instead")
        def old_func():
            return "old"

        result = old_func()
        assert result == "old"


class TestOnce:
    """Test once decorator"""

    def test_once(self):
        """Test once decorator"""
        call_count = 0

        @once
        def run_once():
            nonlocal call_count
            call_count += 1
            return "done"

        assert run_once() == "done"
        assert run_once() == "done"
        assert call_count == 1


class TestRateLimit:
    """Test rate_limit decorator"""

    def test_rate_limit(self):
        """Test rate limit"""
        call_count = 0

        @rate_limit(calls=3, period=1.0)
        def limited_func():
            nonlocal call_count
            call_count += 1
            return "done"

        # First 3 calls should succeed immediately
        for _ in range(3):
            limited_func()

        assert call_count == 3


class TestValidateArgs:
    """Test validate_args decorator"""

    def test_validate_args(self):
        """Test validate args - valid case"""
        @validate_args(x=lambda v: v > 0, y=lambda v: isinstance(v, str))
        def func(x, y):
            return f"{y}: {x}"

        result = func(5, "value")
        assert result == "value: 5"


class TestMemoize:
    """Test memoize decorator"""

    def test_memoize(self):
        """Test memoize"""
        call_count = 0

        @memoize
        def memo_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert memo_func(5) == 10
        assert call_count == 1
        assert memo_func(5) == 10
        assert call_count == 1


class TestAsyncRetry:
    """Test async_retry decorator"""

    @pytest.mark.asyncio
    async def test_async_retry(self):
        """Test async retry"""
        call_count = 0

        @async_retry(max_attempts=3, delay=0.1)
        async def async_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("not yet")
            return "success"

        result = await async_succeed()
        assert result == "success"
        assert call_count == 2


class TestAsyncTiming:
    """Test async_timing decorator"""

    @pytest.mark.asyncio
    async def test_async_timing(self):
        """Test async timing"""

        @async_timing
        async def slow_async():
            await asyncio.sleep(0.05)
            return "done"

        result = await slow_async()
        assert result == "done"
