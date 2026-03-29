"""Tests for Transformers"""


from orchestration.transformers import (
    ChainTransformer,
    DefaultValueTransformer,
    ExcludeKeysTransformer,
    FilterTransformer,
    FlatMapTransformer,
    MapTransformer,
    MergeTransformer,
    RegexReplaceTransformer,
    RenameKeysTransformer,
    SelectKeysTransformer,
    defaults,
    exclude_keys,
    filter_,
    map_,
    merge,
    regex_replace,
    rename_keys,
    select_keys,
    transform,
)


class TestMapTransformer:
    """Test MapTransformer"""

    def test_transform_list(self):
        """Test transform list"""
        t = MapTransformer(lambda x: x * 2)
        result = t.transform([1, 2, 3])
        assert result == [2, 4, 6]

    def test_transform_single(self):
        """Test transform single"""
        t = MapTransformer(lambda x: x.upper())
        result = t.transform("hello")
        assert result == "HELLO"


class TestFilterTransformer:
    """Test FilterTransformer"""

    def test_filter_list(self):
        """Test filter list"""
        t = FilterTransformer(lambda x: x > 5)
        result = t.transform([1, 6, 3, 8, 2])
        assert result == [6, 8]


class TestFlatMapTransformer:
    """Test FlatMapTransformer"""

    def test_flat_map(self):
        """Test flat map"""
        t = FlatMapTransformer(lambda x: [x, x * 2])
        result = t.transform([1, 2, 3])
        assert result == [1, 2, 2, 4, 3, 6]


class TestRenameKeysTransformer:
    """Test RenameKeysTransformer"""

    def test_rename_keys(self):
        """Test rename keys"""
        t = RenameKeysTransformer({"old": "new"})
        result = t.transform({"old": "value", "keep": "data"})
        assert result == {"new": "value", "keep": "data"}


class TestSelectKeysTransformer:
    """Test SelectKeysTransformer"""

    def test_select_keys(self):
        """Test select keys"""
        t = SelectKeysTransformer(["a", "b"])
        result = t.transform({"a": 1, "b": 2, "c": 3})
        assert result == {"a": 1, "b": 2}


class TestExcludeKeysTransformer:
    """Test ExcludeKeysTransformer"""

    def test_exclude_keys(self):
        """Test exclude keys"""
        t = ExcludeKeysTransformer(["c"])
        result = t.transform({"a": 1, "b": 2, "c": 3})
        assert result == {"a": 1, "b": 2}


class TestMergeTransformer:
    """Test MergeTransformer"""

    def test_merge(self):
        """Test merge"""
        t = MergeTransformer({"b": 2}, {"c": 3})
        result = t.transform({"a": 1})
        assert result == {"a": 1, "b": 2, "c": 3}


class TestDefaultValueTransformer:
    """Test DefaultValueTransformer"""

    def test_defaults(self):
        """Test defaults"""
        t = DefaultValueTransformer({"a": 1, "b": 2})
        result = t.transform({"b": 10, "c": 3})
        assert result == {"a": 1, "b": 10, "c": 3}


class TestRegexReplaceTransformer:
    """Test RegexReplaceTransformer"""

    def test_replace_string(self):
        """Test replace in string"""
        t = RegexReplaceTransformer(r"\d+", "NUM")
        result = t.transform("abc 123 def 456")
        assert result == "abc NUM def NUM"

    def test_replace_dict(self):
        """Test replace in dict"""
        t = RegexReplaceTransformer(r"secret", "***")
        result = t.transform({"key": "my secret data"})
        assert result == {"key": "my *** data"}


class TestChainTransformer:
    """Test ChainTransformer"""

    def test_chain(self):
        """Test chain"""
        chain = ChainTransformer(
            MapTransformer(lambda x: x * 2),
            FilterTransformer(lambda x: x > 4),
        )
        result = chain.transform([1, 2, 3, 4, 5])
        assert result == [6, 8, 10]

    def test_add(self):
        """Test add transformer"""
        chain = ChainTransformer(MapTransformer(lambda x: x + 1))
        chain.add(FilterTransformer(lambda x: x > 5))
        result = chain.transform([1, 2, 8, 3])
        assert result == [9]


class TestPipelineFunctions:
    """Test pipeline functions"""

    def test_transform(self):
        """Test transform function"""
        result = transform(
            [1, 2, 3],
            map_(lambda x: x * 2),
            filter_(lambda x: x > 3),
        )
        assert result == [4, 6]

    def test_rename_keys(self):
        """Test rename_keys helper"""
        t = rename_keys({"old": "new"})
        result = t.transform({"old": "value"})
        assert result == {"new": "value"}

    def test_select_keys(self):
        """Test select_keys helper"""
        t = select_keys(["a", "b"])
        result = t.transform({"a": 1, "b": 2, "c": 3})
        assert result == {"a": 1, "b": 2}

    def test_exclude_keys(self):
        """Test exclude_keys helper"""
        t = exclude_keys(["c"])
        result = t.transform({"a": 1, "b": 2, "c": 3})
        assert result == {"a": 1, "b": 2}

    def test_merge(self):
        """Test merge helper"""
        t = merge({"b": 2})
        result = t.transform({"a": 1})
        assert result == {"a": 1, "b": 2}

    def test_defaults(self):
        """Test defaults helper"""
        t = defaults({"a": 1})
        result = t.transform({"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_regex_replace(self):
        """Test regex_replace helper"""
        t = regex_replace(r"foo", "bar")
        result = t.transform("foo foo")
        assert result == "bar bar"
