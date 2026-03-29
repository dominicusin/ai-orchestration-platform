"""Tests for Filters"""


from orchestration.filters import (
    CompositeFilter,
    DedupeFilter,
    KeyFilter,
    LambdaFilter,
    LimitFilter,
    NullFilter,
    RangeFilter,
    RegexFilter,
    SortFilter,
    TypeFilter,
    and_,
    by_key,
    by_range,
    by_regex,
    by_type,
    dedupe,
    filter_,
    limit,
    or_,
    remove_null,
    sort,
)


class TestLambdaFilter:
    """Test LambdaFilter"""

    def test_filter_list(self):
        """Test filter list"""
        f = LambdaFilter(lambda x: x > 5)
        result = f.apply([1, 6, 3, 8, 2])
        assert result == [6, 8]

    def test_filter_single(self):
        """Test filter single"""
        f = LambdaFilter(lambda x: x > 5)
        result = f.apply(10)
        assert result == 10


class TestKeyFilter:
    """Test KeyFilter"""

    def test_filter_list(self):
        """Test filter list"""
        f = KeyFilter("status", "active")
        data = [
            {"name": "a", "status": "active"},
            {"name": "b", "status": "inactive"},
            {"name": "c", "status": "active"},
        ]
        result = f.apply(data)
        assert len(result) == 2


class TestRangeFilter:
    """Test RangeFilter"""

    def test_filter_range(self):
        """Test filter range"""
        f = RangeFilter(5, 10)
        result = f.apply([1, 6, 3, 8, 12])
        assert result == [6, 8]

    def test_filter_with_key(self):
        """Test filter with key"""
        f = RangeFilter(5, 10, key="age")
        data = [{"name": "a", "age": 3}, {"name": "b", "age": 7}, {"name": "c", "age": 12}]
        result = f.apply(data)
        assert len(result) == 1


class TestRegexFilter:
    """Test RegexFilter"""

    def test_filter_regex(self):
        """Test filter regex"""
        f = RegexFilter(r"^test")
        result = f.apply(["test1", "test2", "other"])
        assert result == ["test1", "test2"]


class TestTypeFilter:
    """Test TypeFilter"""

    def test_filter_type(self):
        """Test filter type"""
        f = TypeFilter(int, float)
        result = f.apply([1, "a", 2.5, "b", 3])
        assert result == [1, 2.5, 3]


class TestCompositeFilter:
    """Test CompositeFilter"""

    def test_and_filter(self):
        """Test AND filter"""
        f = CompositeFilter(
            LambdaFilter(lambda x: x > 3),
            LambdaFilter(lambda x: x < 8),
            mode="and",
        )
        result = f.apply([1, 5, 10, 6])
        assert result == [5, 6]

    def test_or_filter(self):
        """Test OR filter"""
        f = CompositeFilter(
            LambdaFilter(lambda x: x > 8),
            LambdaFilter(lambda x: x < 3),
            mode="or",
        )
        result = f.apply([1, 5, 10, 6])
        assert result == [1, 10]


class TestDedupeFilter:
    """Test DedupeFilter"""

    def test_dedupe(self):
        """Test dedupe"""
        f = DedupeFilter()
        result = f.apply([1, 2, 1, 3, 2])
        assert len(result) == 3


class TestSortFilter:
    """Test SortFilter"""

    def test_sort(self):
        """Test sort"""
        f = SortFilter()
        result = f.apply([3, 1, 2])
        assert result == [1, 2, 3]

    def test_sort_reverse(self):
        """Test sort reverse"""
        f = SortFilter(reverse=True)
        result = f.apply([1, 3, 2])
        assert result == [3, 2, 1]

    def test_sort_by_key(self):
        """Test sort by key"""
        f = SortFilter(key="age")
        data = [{"name": "a", "age": 3}, {"name": "b", "age": 1}, {"name": "c", "age": 2}]
        result = f.apply(data)
        assert result[0]["name"] == "b"


class TestLimitFilter:
    """Test LimitFilter"""

    def test_limit(self):
        """Test limit"""
        f = LimitFilter(3)
        result = f.apply([1, 2, 3, 4, 5])
        assert result == [1, 2, 3]

    def test_limit_with_offset(self):
        """Test limit with offset"""
        f = LimitFilter(2, offset=2)
        result = f.apply([1, 2, 3, 4, 5])
        assert result == [3, 4]


class TestNullFilter:
    """Test NullFilter"""

    def test_remove_null(self):
        """Test remove null"""
        f = NullFilter(keep=False)
        result = f.apply([1, None, 2, None, 3])
        assert result == [1, 2, 3]

    def test_keep_null(self):
        """Test keep null"""
        f = NullFilter(keep=True)
        result = f.apply([1, None, 2, None, 3])
        assert result == [None, None]


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_by_key(self):
        """Test by_key"""
        f = by_key("status", "active")
        result = f.apply([{"status": "active"}, {"status": "other"}])
        assert len(result) == 1

    def test_by_range(self):
        """Test by_range"""
        f = by_range(5, 10)
        result = f.apply([1, 6, 11])
        assert result == [6]

    def test_by_regex(self):
        """Test by_regex"""
        f = by_regex(r"^test")
        result = f.apply(["test1", "other"])
        assert result == ["test1"]

    def test_by_type(self):
        """Test by_type"""
        f = by_type(int)
        result = f.apply([1, "a", 2])
        assert result == [1, 2]

    def test_filter(self):
        """Test filter helper"""
        f = filter_(lambda x: x > 0)
        result = f.apply([-1, 1, -2, 2])
        assert result == [1, 2]

    def test_and(self):
        """Test and_ helper"""
        f = and_(LambdaFilter(lambda x: x > 3), LambdaFilter(lambda x: x < 10))
        result = f.apply([1, 5, 15])
        assert result == [5]

    def test_or(self):
        """Test or_ helper"""
        f = or_(LambdaFilter(lambda x: x < 3), LambdaFilter(lambda x: x > 10))
        result = f.apply([1, 5, 15])
        assert result == [1, 15]

    def test_dedupe(self):
        """Test dedupe helper"""
        f = dedupe()
        result = f.apply([1, 2, 1])
        assert len(result) == 2

    def test_sort(self):
        """Test sort helper"""
        f = sort()
        result = f.apply([3, 1, 2])
        assert result == [1, 2, 3]

    def test_limit(self):
        """Test limit helper"""
        f = limit(3)
        result = f.apply([1, 2, 3, 4, 5])
        assert result == [1, 2, 3]

    def test_remove_null(self):
        """Test remove_null helper"""
        f = remove_null()
        result = f.apply([1, None, 2])
        assert result == [1, 2]
