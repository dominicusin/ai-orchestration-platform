"""Tests for Utils Helpers"""

import os
from pathlib import Path

from orchestration.utils_helpers import (
    ConfigProxy,
    LazyLoader,
    chunk_list,
    deep_get,
    deep_set,
    ensure_config_dir,
    flatten_dict,
    get_config_dir,
    get_cpu_count,
    get_env,
    get_hostname,
    get_pid,
    get_project_root,
    get_version,
    is_debug,
    is_production,
    merge_dicts,
    set_env,
    truncate,
    unique_list,
)


class TestEnvFunctions:
    """Test env functions"""

    def test_get_env(self):
        """Test get env"""
        os.environ["TEST_VAR"] = "test_value"
        assert get_env("TEST_VAR") == "test_value"
        assert get_env("MISSING", "default") == "default"

    def test_set_env(self):
        """Test set env"""
        set_env("NEW_VAR", "new_value")
        assert os.environ["NEW_VAR"] == "new_value"


class TestPathFunctions:
    """Test path functions"""

    def test_get_project_root(self):
        """Test get project root"""
        root = get_project_root()
        assert isinstance(root, Path)

    def test_get_config_dir(self):
        """Test get config dir"""
        config_dir = get_config_dir()
        assert isinstance(config_dir, Path)

    def test_ensure_config_dir(self):
        """Test ensure config dir"""
        config_dir = ensure_config_dir()
        assert config_dir.exists()


class TestInfoFunctions:
    """Test info functions"""

    def test_get_version(self):
        """Test get version"""
        version = get_version()
        assert isinstance(version, str)

    def test_is_debug(self):
        """Test is debug"""
        result = is_debug()
        assert isinstance(result, bool)

    def test_is_production(self):
        """Test is production"""
        result = is_production()
        assert isinstance(result, bool)

    def test_get_hostname(self):
        """Test get hostname"""
        hostname = get_hostname()
        assert isinstance(hostname, str)

    def test_get_pid(self):
        """Test get pid"""
        pid = get_pid()
        assert isinstance(pid, int)
        assert pid > 0

    def test_get_cpu_count(self):
        """Test get cpu count"""
        count = get_cpu_count()
        assert isinstance(count, int)
        assert count >= 1


class TestStringFunctions:
    """Test string functions"""

    def test_truncate_short(self):
        """Test truncate short text"""
        text = "short"
        result = truncate(text, 10)
        assert result == "short"

    def test_truncate_long(self):
        """Test truncate long text"""
        text = "a" * 200
        result = truncate(text, 10)
        assert len(result) <= 13
        assert result.endswith("...")


class TestDictFunctions:
    """Test dict functions"""

    def test_deep_get(self):
        """Test deep get"""
        d = {"a": {"b": {"c": "value"}}}
        assert deep_get(d, "a.b.c") == "value"
        assert deep_get(d, "a.b.d", "default") == "default"

    def test_deep_set(self):
        """Test deep set"""
        d = {}
        deep_set(d, "a.b.c", "value")
        assert d["a"]["b"]["c"] == "value"

    def test_merge_dicts(self):
        """Test merge dicts"""
        d1 = {"a": 1}
        d2 = {"b": 2}
        d3 = {"a": 10}
        result = merge_dicts(d1, d2, d3)
        assert result == {"a": 10, "b": 2}

    def test_flatten_dict(self):
        """Test flatten dict"""
        d = {"a": {"b": 1, "c": 2}, "d": 3}
        result = flatten_dict(d)
        assert result == {"a.b": 1, "a.c": 2, "d": 3}


class TestListFunctions:
    """Test list functions"""

    def test_chunk_list(self):
        """Test chunk list"""
        lst = [1, 2, 3, 4, 5, 6, 7]
        result = chunk_list(lst, 3)
        assert result == [[1, 2, 3], [4, 5, 6], [7]]

    def test_unique_list(self):
        """Test unique list"""
        lst = [1, 2, 1, 3, 2, 4]
        result = unique_list(lst)
        assert result == [1, 2, 3, 4]


class TestLazyLoader:
    """Test LazyLoader"""

    def test_lazy_loader(self):
        """Test lazy loader"""
        loaded = []

        def loader():
            loaded.append(1)
            return "loaded"

        lazy = LazyLoader(loader)
        assert len(loaded) == 0

        result = lazy.get()
        assert result == "loaded"
        assert len(loaded) == 1

        # Second call should not reload
        result = lazy.get()
        assert len(loaded) == 1


class TestConfigProxy:
    """Test ConfigProxy"""

    def test_config_proxy(self):
        """Test config proxy"""
        config = {"key": "value", "nested": {"inner": "data"}}
        proxy = ConfigProxy(config)

        assert proxy.get("key") == "value"
        assert proxy.key == "value"
        assert proxy["key"] == "value"
