"""Tests for A/B Testing"""


import pytest

from orchestration.ab_testing import (
    ABTestingManager,
    ABTestResult,
    ABTestStats,
    ABTestVariant,
)


class TestABTestVariant:
    """Test ABTestVariant dataclass"""

    def test_creation(self):
        """Test variant creation"""
        variant = ABTestVariant(
            id="v1",
            name="Variant A",
            prompt_name="cpp_to_haskell",
            prompt_version="1.0.0",
            weight=50,
        )
        assert variant.id == "v1"
        assert variant.weight == 50
        assert variant.enabled is True


class TestABTestResult:
    """Test ABTestResult dataclass"""

    def test_creation(self):
        """Test result creation"""
        result = ABTestResult(
            variant_id="v1",
            success=True,
            response_time=1.5,
            quality_score=0.9,
            tokens_used=100,
        )
        assert result.variant_id == "v1"
        assert result.success is True
        assert result.response_time == 1.5


class TestABTestStats:
    """Test ABTestStats dataclass"""

    def test_success_rate(self):
        """Test success rate calculation"""
        stats = ABTestStats(
            test_id="test1",
            variant_id="v1",
            impressions=10,
            successes=7,
            failures=3,
        )
        assert stats.success_rate == 0.7

    def test_avg_response_time(self):
        """Test avg response time calculation"""
        stats = ABTestStats(
            test_id="test1",
            variant_id="v1",
            impressions=10,
            total_response_time=15.0,
        )
        assert stats.avg_response_time == 1.5

    def test_avg_quality(self):
        """Test avg quality calculation"""
        stats = ABTestStats(
            test_id="test1",
            variant_id="v1",
            successes=5,
            total_quality_score=4.5,
        )
        assert stats.avg_quality == 0.9


class TestABTestingManager:
    """Test A/B Testing Manager"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temp results directory"""
        return tmp_path / "ab_results"

    @pytest.fixture
    def manager(self, temp_dir):
        """Create manager with temp directory"""
        return ABTestingManager(temp_dir)

    @pytest.fixture
    def sample_variants(self):
        """Sample variants for testing"""
        return [
            ABTestVariant(
                id="v1",
                name="Variant A",
                prompt_name="test_prompt",
                prompt_version="1.0.0",
                weight=50,
            ),
            ABTestVariant(
                id="v2",
                name="Variant B",
                prompt_name="test_prompt",
                prompt_version="1.1.0",
                weight=50,
            ),
        ]

    def test_manager_init(self, manager):
        """Test manager initialization"""
        assert manager.results_dir.exists()

    def test_create_test(self, manager, sample_variants):
        """Test create A/B test"""
        result = manager.create_test("test1", sample_variants)
        assert result is True
        assert "test1" in manager._tests
        assert len(manager._tests["test1"]) == 2

    def test_create_test_min_variants(self, manager):
        """Test create test with less than 2 variants"""
        variants = [
            ABTestVariant("v1", "V1", "p", "1.0", 100),
        ]
        result = manager.create_test("test1", variants)
        assert result is False

    def test_select_variant(self, manager, sample_variants):
        """Test variant selection"""
        manager.create_test("test1", sample_variants)

        # Select multiple times
        selected = []
        for _ in range(100):
            variant = manager.select_variant("test1")
            if variant:
                selected.append(variant.id)

        # Both variants should be selected
        assert "v1" in selected
        assert "v2" in selected

    def test_select_variant_disabled(self, manager, sample_variants):
        """Test variant selection with disabled variants"""
        manager.create_test("test1", sample_variants)
        manager.stop_test("test1")

        variant = manager.select_variant("test1")
        assert variant is None

    def test_record_result(self, manager, sample_variants):
        """Test recording result"""
        manager.create_test("test1", sample_variants)
        manager.select_variant("test1")  # This records impression

        result = ABTestResult(
            variant_id="v1",
            success=True,
            response_time=1.0,
            quality_score=0.8,
            tokens_used=50,
        )
        manager.record_result("test1", result)

        stats = manager.get_stats("test1")
        assert stats["v1"].successes == 1
        assert stats["v1"].total_response_time == 1.0

    def test_get_winner(self, manager, sample_variants):
        """Test get winner"""
        manager.create_test("test1", sample_variants)

        # Record results favoring v1
        for _ in range(10):
            manager.select_variant("test1")

        result = ABTestResult(variant_id="v1", success=True, response_time=1.0)
        manager.record_result("test1", result)

        result2 = ABTestResult(variant_id="v2", success=False, response_time=1.0)
        manager.record_result("test1", result2)

        winner = manager.get_winner("test1")
        assert winner is not None
        assert winner.id == "v1"

    def test_get_leaderboard(self, manager, sample_variants):
        """Test leaderboard"""
        manager.create_test("test1", sample_variants)

        # Record some results
        for i in range(10):
            variant = manager.select_variant("test1")
            if variant:
                result = ABTestResult(
                    variant_id=variant.id,
                    success=i < 7,
                    response_time=1.0,
                )
                manager.record_result("test1", result)

        leaderboard = manager.get_leaderboard("test1")
        assert len(leaderboard) == 2
        # First variant should have higher success rate
        assert float(leaderboard[0]["success_rate"].rstrip("%")) >= 50

    def test_stop_test(self, manager, sample_variants):
        """Test stop test"""
        manager.create_test("test1", sample_variants)
        result = manager.stop_test("test1")
        assert result is True

        # Check all variants disabled
        for v in manager._tests["test1"]:
            assert v.enabled is False

    def test_delete_test(self, manager, sample_variants):
        """Test delete test"""
        manager.create_test("test1", sample_variants)
        result = manager.delete_test("test1")
        assert result is True
        assert "test1" not in manager._tests

    def test_list_tests(self, manager, sample_variants):
        """Test list tests"""
        manager.create_test("test1", sample_variants)
        manager.create_test("test2", sample_variants)

        tests = manager.list_tests()
        assert len(tests) == 2
        assert "test1" in tests
        assert "test2" in tests

    def test_select_nonexistent_test(self, manager):
        """Test select variant for nonexistent test"""
        variant = manager.select_variant("nonexistent")
        assert variant is None
