"""Tests for Cache Invalidation"""

import time

import pytest

from orchestration.cache_invalidation import (
    CacheEntry,
    CacheInvalidator,
    TTLCache,
    get_ttl_cache,
)


class TestCacheEntry:
    """Test CacheEntry"""

    def test_creation(self):
        """Test creation"""
        entry = CacheEntry(key="test", value="value")
        assert entry.key == "test"
        assert entry.value == "value"
        assert entry.hit_count == 0


class TestCacheInvalidator:
    """Test CacheInvalidator"""

    @pytest.fixture
    def invalidator(self):
        """Create invalidator"""
        return CacheInvalidator()

    def test_creation(self, invalidator):
        """Test creation"""
        assert invalidator is not None

    def test_invalidate(self, invalidator):
        """Test invalidate"""
        invalidator._entries["key1"] = CacheEntry(key="key1", value="value1")
        invalidator.invalidate("key1", "manual")
        assert "key1" not in invalidator._entries

    def test_invalidate_missing(self, invalidator):
        """Test invalidate missing key"""
        invalidator.invalidate("missing", "manual")  # Should not raise

    def test_invalidate_pattern(self, invalidator):
        """Test invalidate pattern"""
        invalidator._entries["test1"] = CacheEntry(key="test1", value="v1")
        invalidator._entries["test2"] = CacheEntry(key="test2", value="v2")
        invalidator._entries["other"] = CacheEntry(key="other", value="v3")

        invalidator.invalidate_pattern(r"test\d+", "pattern")

        assert "test1" not in invalidator._entries
        assert "test2" not in invalidator._entries
        assert "other" in invalidator._entries

    def test_invalidate_tag(self, invalidator):
        """Test invalidate tag"""
        invalidator._entries["key1"] = CacheEntry(key="key1", value="v1", tags={"tag1"})
        invalidator._entries["key2"] = CacheEntry(key="key2", value="v2", tags={"tag2"})
        invalidator._entries["key3"] = CacheEntry(key="key3", value="v3", tags={"tag1"})

        invalidator.invalidate_tag("tag1", "tag")

        assert "key1" not in invalidator._entries
        assert "key2" in invalidator._entries
        assert "key3" not in invalidator._entries

    def test_invalidate_old(self, invalidator):
        """Test invalidate older than"""
        invalidator._entries["old"] = CacheEntry(key="old", value="v", created_at=time.time() - 100)
        invalidator._entries["new"] = CacheEntry(key="new", value="v", created_at=time.time())

        invalidator.invalidate_older_than(50, "ttl")

        assert "old" not in invalidator._entries
        assert "new" in invalidator._entries

    def test_invalidate_least_used(self, invalidator):
        """Test invalidate least used"""
        invalidator._entries["key1"] = CacheEntry(key="key1", value="v", hit_count=1)
        invalidator._entries["key2"] = CacheEntry(key="key2", value="v", hit_count=10)
        invalidator._entries["key3"] = CacheEntry(key="key3", value="v", hit_count=5)

        invalidator.invalidate_least_used(2, "lru")

        # Should remove 2 least used (key1 and key3)
        assert "key1" not in invalidator._entries
        assert "key3" not in invalidator._entries
        assert "key2" in invalidator._entries

    def test_clear_all(self, invalidator):
        """Test clear all"""
        invalidator._entries["key1"] = CacheEntry(key="key1", value="v1")
        invalidator._entries["key2"] = CacheEntry(key="key2", value="v2")

        invalidator.clear_all("clear")

        assert len(invalidator._entries) == 0

    def test_listener(self, invalidator):
        """Test listener"""
        notifications = []

        def listener(key, reason):
            notifications.append((key, reason))

        invalidator.register_listener(listener)
        invalidator._entries["key1"] = CacheEntry(key="key1", value="v1")
        invalidator.invalidate("key1", "manual")

        assert len(notifications) == 1
        assert notifications[0] == ("key1", "manual")

    def test_get_stats(self, invalidator):
        """Test get stats"""
        invalidator._entries["key1"] = CacheEntry(key="key1", value="v1", hit_count=5)
        invalidator._entries["key2"] = CacheEntry(key="key2", value="v2", hit_count=10)

        stats = invalidator.get_stats()
        assert stats["total_entries"] == 2
        assert stats["total_hits"] == 15


class TestTTLCache:
    """Test TTLCache"""

    @pytest.fixture
    def cache(self):
        """Create cache"""
        return TTLCache(default_ttl=1)

    def test_creation(self, cache):
        """Test creation"""
        assert cache.default_ttl == 1

    def test_set_get(self, cache):
        """Test set/get"""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing(self, cache):
        """Test get missing"""
        assert cache.get("missing") is None

    def test_expire(self, cache):
        """Test expire"""
        cache.set("key1", "value1", ttl=0.1)
        time.sleep(0.2)
        assert cache.get("key1") is None

    def test_delete(self, cache):
        """Test delete"""
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_clear(self, cache):
        """Test clear"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None

    def test_invalidate_pattern(self, cache):
        """Test invalidate pattern"""
        cache.set("test1", "v1")
        cache.set("test2", "v2")
        cache.set("other", "v3")

        cache.invalidate_pattern(r"test\d+")

        assert cache.get("test1") is None
        assert cache.get("test2") is None
        assert cache.get("other") == "v3"

    def test_invalidate_tag(self, cache):
        """Test invalidate tag"""
        cache.set("key1", "v1", tags=["tag1"])
        cache.set("key2", "v2", tags=["tag2"])

        cache.invalidate_tag("tag1")

        assert cache.get("key1") is None
        assert cache.get("key2") == "v2"


class TestTTLCacheSingleton:
    """Test singleton"""

    def test_singleton(self):
        """Test singleton"""
        c1 = get_ttl_cache()
        c2 = get_ttl_cache()
        assert c1 is c2
