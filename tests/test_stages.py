"""Tests for Stages"""

import pytest
import asyncio

from orchestration.stages import (
    StageStatus,
    StageResult,
    Stage,
    Pipeline,
    StageBuilder,
    create_pipeline,
    create_stage_builder,
)


class TestStageStatus:
    """Test StageStatus"""

    def test_values(self):
        """Test enum values"""
        assert StageStatus.PENDING.value == "pending"
        assert StageStatus.RUNNING.value == "running"
        assert StageStatus.COMPLETED.value == "completed"
        assert StageStatus.FAILED.value == "failed"


class TestStageResult:
    """Test StageResult"""

    def test_creation(self):
        """Test creation"""
        result = StageResult(status=StageStatus.COMPLETED, output="test")
        assert result.status == StageStatus.COMPLETED
        assert result.output == "test"


class TestStage:
    """Test Stage"""

    def test_creation(self):
        """Test creation"""
        def func():
            return "test"

        stage = Stage(name="test", func=func)
        assert stage.name == "test"
        assert stage.status == StageStatus.PENDING

    def test_is_completed(self):
        """Test is_completed"""
        stage = Stage(name="test", func=lambda: None, status=StageStatus.COMPLETED)
        assert stage.is_completed() is True

    def test_is_failed(self):
        """Test is_failed"""
        stage = Stage(name="test", func=lambda: None, status=StageStatus.FAILED)
        assert stage.is_failed() is True

    def test_is_running(self):
        """Test is_running"""
        stage = Stage(name="test", func=lambda: None, status=StageStatus.RUNNING)
        assert stage.is_running() is True


class TestPipeline:
    """Test Pipeline"""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline"""
        return Pipeline("test")

    def test_creation(self):
        """Test creation"""
        p = Pipeline("test")
        assert p.name == "test"

    def test_add_stage(self, pipeline):
        """Test add stage"""
        pipeline.add_stage("s1", lambda: "result")
        assert pipeline.get_stage("s1") is not None

    def test_remove_stage(self, pipeline):
        """Test remove stage"""
        pipeline.add_stage("s1", lambda: None)
        assert pipeline.remove_stage("s1") is True
        assert pipeline.get_stage("s1") is None

    def test_get_ready_stages(self, pipeline):
        """Test get ready stages"""
        pipeline.add_stage("s1", lambda: None)
        pipeline.add_stage("s2", lambda: None, dependencies=["s1"])
        ready = pipeline.get_ready_stages()
        assert "s1" in ready

    def test_execute_simple(self, pipeline):
        """Test execute simple"""
        pipeline.add_stage("s1", lambda: "result")
        results = pipeline.execute()
        assert "s1" in results
        assert results["s1"].status == StageStatus.COMPLETED

    def test_execute_with_deps(self, pipeline):
        """Test execute with dependencies"""
        pipeline.add_stage("s1", lambda: 1)
        pipeline.add_stage("s2", lambda: 2)
        pipeline.add_stage("s3", lambda: 3, dependencies=["s2"])
        results = pipeline.execute()
        assert results["s3"].status == StageStatus.COMPLETED

    def test_list_stages(self, pipeline):
        """Test list stages"""
        pipeline.add_stage("s1", lambda: None)
        pipeline.add_stage("s2", lambda: None)
        stages = pipeline.list_stages()
        assert len(stages) == 2

    def test_get_status_summary(self, pipeline):
        """Test get status summary"""
        pipeline.add_stage("s1", lambda: None)
        pipeline.add_stage("s2", lambda: None)
        summary = pipeline.get_status_summary()
        assert summary["total"] == 2


class TestAsyncPipeline:
    """Test async pipeline"""

    @pytest.mark.asyncio
    async def test_execute_async(self):
        """Test execute async"""
        pipeline = Pipeline("test")

        async def async_func():
            await asyncio.sleep(0.01)
            return "result"

        pipeline.add_stage("s1", async_func)
        results = await pipeline.execute_async()
        assert results["s1"].status == StageStatus.COMPLETED


class TestStageBuilder:
    """Test StageBuilder"""

    def test_creation(self):
        """Test creation"""
        builder = create_stage_builder("test")
        assert builder is not None

    def test_stage(self):
        """Test stage"""
        builder = create_stage_builder("test")
        builder.stage("s1", lambda: None)
        assert builder._pipeline.get_stage("s1") is not None


class TestHelperFunctions:
    """Test helper functions"""

    def test_create_pipeline(self):
        """Test create_pipeline"""
        p = create_pipeline("test")
        assert isinstance(p, Pipeline)

    def test_create_stage_builder(self):
        """Test create_stage_builder"""
        b = create_stage_builder("test")
        assert isinstance(b, StageBuilder)
