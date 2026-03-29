"""Tests for Redis cache"""

from unittest.mock import MagicMock, patch

import pytest

from orchestration.cache.redis_cache import (
    RedisCache,
    RedisCacheConfig,
)


class TestRedisCacheConfig:
    """Test Redis cache configuration"""

    def test_from_env(self):
        """Test config from env"""
        with patch.dict("os.environ", {
            "REDIS_HOST": "redis.example.com",
            "REDIS_PORT": "6380",
            "REDIS_DB": "1",
            "REDIS_PASSWORD": "secret",
            "REDIS_KEY_PREFIX": "test:",
            "REDIS_TTL": "3600",
        }):
            config = RedisCacheConfig.from_env()
            assert config.host == "redis.example.com"
            assert config.port == 6380
            assert config.db == 1
            assert config.password == "secret"
            assert config.key_prefix == "test:"
            assert config.default_ttl == 3600

    def test_config_defaults(self):
        """Test config defaults"""
        config = RedisCacheConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.ssl is False
        assert config.key_prefix == "ai_pipeline:"
        assert config.default_ttl == 86400 * 7  # 7 days


class TestRedisCache:
    """Test Redis cache"""

    @pytest.fixture
    def config(self):
        """Create test config"""
        return RedisCacheConfig(host="localhost", port=6379)

    @pytest.fixture
    def cache(self, config):
        """Create cache with test config"""
        return RedisCache(config)

    def test_cache_init(self, cache, config):
        """Test cache initialization"""
        assert cache.config == config
        assert cache.policy.value == "cache_first"
        assert cache._connected is False

    def test_get_key(self, cache):
        """Test key generation"""
        key = cache._get_key("/path/to/file.cpp", "haskell")
        assert isinstance(key, str)
        assert key.startswith("ai_pipeline:haskell:")

    def test_get_source_hash(self, cache):
        """Test source hash"""
        content = "test content"
        hash1 = cache._get_source_hash(content)
        hash2 = cache._get_source_hash(content)
        assert hash1 == hash2
        assert len(hash1) == 32  # md5 hex

    def test_get_source_hash_different(self, cache):
        """Test different content produces different hash"""
        hash1 = cache._get_source_hash("content 1")
        hash2 = cache._get_source_hash("content 2")
        assert hash1 != hash2

    @patch("orchestration.cache.redis_cache.redis.Redis")
    def test_connect_success(self, mock_redis, cache):
        """Test successful connection"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        result = cache.connect()
        assert result is True
        assert cache._connected is True

    @patch("orchestration.cache.redis_cache.redis.Redis")
    def test_connect_failure(self, mock_redis, cache):
        """Test connection failure"""
        import redis
        mock_redis.side_effect = redis.ConnectionError("Connection refused")

        result = cache.connect()
        assert result is False
        assert cache._connected is False

    def test_get_without_connection(self, cache):
        """Test get without connection"""
        result = cache.get("/path/file.cpp", "haskell", "content")
        assert result is None

    def test_set_without_connection(self, cache):
        """Test set without connection"""
        # Should not raise
        cache.set("/path/file.cpp", "haskell", "content", "result")

    def test_invalidate_without_connection(self, cache):
        """Test invalidate without connection"""
        # Should not raise
        cache.invalidate("/path/file.cpp", "haskell")

    def test_clear_without_connection(self, cache):
        """Test clear without connection"""
        # Should not raise
        cache.clear()

    def test_get_stats(self, cache):
        """Test get stats"""
        stats = cache.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "writes" in stats
        assert "connected" in stats
        assert stats["connected"] is False

    def test_get_redis_info_without_connection(self, cache):
        """Test get redis info without connection"""
        result = cache.get_redis_info()
        assert result is None

    def test_disconnect(self, cache):
        """Test disconnect"""
        cache.disconnect()
        assert cache._connected is False

    @patch("orchestration.cache.redis_cache.redis.Redis")
    def test_disconnect_with_client(self, mock_redis, cache):
        """Test disconnect with client"""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        cache.connect()
        cache.disconnect()
        mock_client.close.assert_called_once()


class TestRedisCacheWithLocalFallback:
    """Test Redis cache with local fallback"""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create cache with local fallback"""
        config = RedisCacheConfig()
        from orchestration.cache.cache import CachePolicy
        return RedisCache(config, CachePolicy.CACHE_FIRST, tmp_path)

    def test_cache_with_local_fallback(self, cache):
        """Test cache with local fallback"""
        assert cache._local_cache is not None

    def test_get_stats_with_local(self, cache):
        """Test get stats with local cache"""
        stats = cache.get_stats()
        assert "local_cache" in stats
