"""Tests for Pipelines"""

import pytest
import asyncio

from orchestration.pipelines import (
    PipelineStage,
    TransformStage,
    FilterStage,
    MapStage,
    FlatMapStage,
    ReduceStage,
    Pipeline,
    AsyncPipeline,
    PipelineBuilder,
    create_pipeline,
    create_async_pipeline,
)


class TestTransformStage:
    """Test TransformStage"""

    def test_creation(self):
        """Test creation"""
        stage = TransformStage("double", lambda x: x * 2)
        assert stage.name == "double"

    def test_process(self):
        """Test process"""
        stage = TransformStage("double", lambda x: x * 2)
        result = stage.process(5)
        assert result == 10


class TestFilterStage:
    """Test FilterStage"""

    def test_creation(self):
        """Test creation"""
        stage = FilterStage("even", lambda x: x % 2 == 0)
        assert stage.name == "even"

    def test_process_keep(self):
        """Test process - keep"""
        stage = FilterStage("even", lambda x: x % 2 == 0)
        result = stage.process(4)
        assert result == 4

    def test_process_filter(self):
        """Test process - filter out"""
        stage = FilterStage("even", lambda x: x % 2 == 0)
        with pytest.raises(StopIteration):
            stage.process(3)


class TestMapStage:
    """Test MapStage"""

    def test_creation(self):
        """Test creation"""
        stage = MapStage("square", lambda x: x ** 2)
        assert stage.name == "square"

    def test_process(self):
        """Test process"""
        stage = MapStage("square", lambda x: x ** 2)
        result = stage.process(3)
        assert result == 9


class TestFlatMapStage:
    """Test FlatMapStage"""

    def test_creation(self):
        """Test creation"""
        stage = FlatMapStage("split", lambda x: list(x))
        assert stage.name == "split"

    def test_process(self):
        """Test process"""
        stage = FlatMapStage("split", lambda x: list(x))
        result = stage.process("abc")
        assert result == ["a", "b", "c"]


class TestReduceStage:
    """Test ReduceStage"""

    def test_creation(self):
        """Test creation"""
        stage = ReduceStage("sum", lambda a, b: a + b, initial=0)
        assert stage.name == "sum"

    def test_process(self):
        """Test process"""
        stage = ReduceStage("sum", lambda a, b: a + b, initial=0)
        result = stage.process([1, 2, 3, 4])
        assert result == 10


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
        stage = TransformStage("t1", lambda x: x)
        pipeline.add_stage(stage)
        assert len(pipeline._stages) == 1

    def test_transform(self, pipeline):
        """Test transform"""
        pipeline.transform("double", lambda x: x * 2)
        result = pipeline.process(5)
        assert result == 10

    def test_filter(self, pipeline):
        """Test filter"""
        pipeline.filter("even", lambda x: x % 2 == 0)
        result = pipeline.process(4)
        assert result == 4

    def test_map(self, pipeline):
        """Test map"""
        pipeline.map("square", lambda x: x ** 2)
        result = pipeline.process(3)
        assert result == 9

    def test_flat_map(self, pipeline):
        """Test flat_map"""
        pipeline.flat_map("split", lambda x: list(x))
        result = pipeline.process("ab")
        assert result == ["a", "b"]

    def test_reduce(self, pipeline):
        """Test reduce"""
        pipeline.reduce("sum", lambda a, b: a + b, 0)
        result = pipeline.process([1, 2, 3])
        assert result == 6

    def test_process_batch(self, pipeline):
        """Test process_batch"""
        pipeline.map("double", lambda x: x * 2)
        results = pipeline.process_batch([1, 2, 3])
        assert results == [2, 4, 6]

    def test_on_error(self, pipeline):
        """Test on_error"""
        errors = []

        def error_handler(e, stage):
            errors.append(str(e))

        pipeline.on_error(error_handler)
        pipeline.transform("fail", lambda x: 1 / 0)
        pipeline.process(1)  # Should not raise


class TestAsyncPipeline:
    """Test AsyncPipeline"""

    @pytest.mark.asyncio
    async def test_creation(self):
        """Test creation"""
        p = AsyncPipeline("test")
        assert p.name == "test"

    @pytest.mark.asyncio
    async def test_process(self):
        """Test process"""
        p = AsyncPipeline("test")
        p.add_stage(TransformStage("double", lambda x: x * 2))
        result = await p.process(5)
        assert result == 10


class TestPipelineBuilder:
    """Test PipelineBuilder"""

    def test_creation(self):
        """Test creation"""
        builder = PipelineBuilder("test")
        assert builder._pipeline.name == "test"

    def test_transform(self):
        """Test transform"""
        builder = PipelineBuilder("test")
        builder.transform("double", lambda x: x * 2)
        p = builder.build()
        result = p.process(5)
        assert result == 10

    def test_filter(self):
        """Test filter"""
        builder = PipelineBuilder("test")
        builder.filter("even", lambda x: x % 2 == 0)
        p = builder.build()
        result = p.process(4)
        assert result == 4


class TestHelperFunctions:
    """Test helper functions"""

    def test_create_pipeline(self):
        """Test create_pipeline"""
        p = create_pipeline("test")
        assert isinstance(p, Pipeline)

    def test_create_async_pipeline(self):
        """Test create_async_pipeline"""
        p = create_async_pipeline("test")
        assert isinstance(p, AsyncPipeline)