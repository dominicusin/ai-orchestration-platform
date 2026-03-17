"""Distributed data processing with recursive task decomposition"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp

logger = logging.getLogger("orchestration.processing")


T = TypeVar('T')
R = TypeVar('R')


@dataclass
class ProcessingTask(Generic[T, R]):
    """Processing task"""
    id: str
    input_data: T
    processor: Callable[[T], R]
    dependencies: List[str] = field(default_factory=list)
    

@dataclass
class ProcessingResult(Generic[R]):
    """Task result"""
    task_id: str
    success: bool
    result: Optional[R] = None
    error: Optional[str] = None
    duration: float = 0


class TaskDecomposer:
    """Recursively decompose large tasks"""
    
    @staticmethod
    def decompose_list(
        items: List[Any],
        max_chunk_size: int = 100,
        min_chunk_size: int = 10,
    ) -> List[List[Any]]:
        """Decompose list into chunks recursively"""
        if len(items) <= max_chunk_size:
            return [items] if items else []
        
        # Split into halves recursively
        mid = len(items) // 2
        left = TaskDecomposer.decompose_list(
            items[:mid], max_chunk_size, min_chunk_size
        )
        right = TaskDecomposer.decompose_list(
            items[mid:], max_chunk_size, min_chunk_size
        )
        
        return left + right
    
    @staticmethod
    def decompose_tree(
        data: Dict,
        leaf_predicate: Callable[[Any], bool],
    ) -> List[Dict]:
        """Decompose tree structure"""
        if leaf_predicate(data):
            return [data]
        
        results = []
        
        if isinstance(data, dict):
            for value in data.values():
                results.extend(TaskDecomposer.decompose_tree(value, leaf_predicate))
        elif isinstance(data, (list, tuple)):
            for item in data:
                results.extend(TaskDecomposer.decompose_tree(item, leaf_predicate))
        
        return results


class ChunkProcessor(Generic[T, R]):
    """Process chunks of data"""
    
    def __init__(self, processor: Callable[[T], R]):
        self.processor = processor
    
    def process_chunk(self, chunk: List[T]) -> List[R]:
        """Process a chunk"""
        return [self.processor(item) for item in chunk]
    
    async def process_chunk_async(self, chunk: List[T]) -> List[R]:
        """Process chunk async"""
        return await asyncio.to_thread(self.process_chunk, chunk)


class DistributedProcessor(Generic[T, R]):
    """Distributed processor with DAG"""
    
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        self.results: Dict[str, ProcessingResult] = {}
    
    def process(
        self,
        items: List[T],
        processor: Callable[[T], R],
        chunk_size: int = 100,
    ) -> List[R]:
        """Process items in parallel chunks"""
        # Decompose into chunks
        chunks = TaskDecomposer.decompose_list(items, chunk_size)
        
        results = []
        
        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            chunk_results = list(executor.map(
                lambda chunk: [processor(item) for item in chunk],
                chunks
            ))
        
        # Flatten results
        for chunk_result in chunk_results:
            results.extend(chunk_result)
        
        return results
    
    async def process_async(
        self,
        items: List[T],
        processor: Callable[[T], R],
        chunk_size: int = 100,
    ) -> List[R]:
        """Process items async"""
        chunks = TaskDecomposer.decompose_list(items, chunk_size)
        
        async def process_chunk(chunk):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                lambda: [processor(item) for item in chunk]
            )
        
        chunk_results = await asyncio.gather(*[
            process_chunk(chunk) for chunk in chunks
        ])
        
        return [item for chunk in chunk_results for item in chunk]
    
    def process_dag(
        self,
        tasks: List[ProcessingTask],
    ) -> Dict[str, ProcessingResult]:
        """Process DAG of tasks"""
        # Build adjacency
        in_degree = defaultdict(int)
        dependents = defaultdict(list)
        
        for task in tasks:
            in_degree[task.id] = len(task.dependencies)
            for dep in task.dependencies:
                dependents[dep].append(task.id)
        
        # Process in topological order
        results = {}
        pending = {t.id: t for t in tasks}
        
        while pending:
            # Find tasks with no pending dependencies
            ready = [
                tid for tid, deg in in_degree.items()
                if deg == 0 and tid in pending
            ]
            
            if not ready:
                break
            
            # Execute ready tasks
            for task_id in ready:
                task = pending.pop(task_id)
                
                try:
                    result = task.processor(task.input_data)
                    results[task_id] = ProcessingResult(
                        task_id=task_id,
                        success=True,
                        result=result,
                    )
                except Exception as e:
                    results[task_id] = ProcessingResult(
                        task_id=task_id,
                        success=False,
                        error=str(e),
                    )
                
                # Update dependent tasks
                for dependent_id in dependents[task_id]:
                    in_degree[dependent_id] -= 1
        
        self.results = results
        return results
    
    def shutdown(self):
        """Shutdown executor"""
        self.executor.shutdown(wait=True)


class MapReduceProcessor(Generic[T, R]):
    """MapReduce-style processor"""
    
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
    
    def map_reduce(
        self,
        items: List[T],
        mapper: Callable[[T], R],
        reducer: Callable[[List[R]], R],
    ) -> R:
        """MapReduce processing"""
        # Map phase
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            mapped = list(executor.map(mapper, items))
        
        # Reduce phase
        return reducer(mapped)
    
    def map_reduce_grouped(
        self,
        items: List[T],
        key_func: Callable[[T], str],
        mapper: Callable[[T], R],
        reducer: Callable[[List[R]], R],
    ) -> Dict[str, R]:
        """MapReduce with grouping"""
        # Group by key
        groups = defaultdict(list)
        for item in items:
            groups[key_func(item)].append(item)
        
        # Process each group
        results = {}
        
        for key, group_items in groups.items():
            mapped = [mapper(item) for item in group_items]
            results[key] = reducer(mapped)
        
        return results


class PipelineProcessor(Generic[T]):
    """Pipeline processor with stages"""
    
    def __init__(self, stages: List[Callable]):
        self.stages = stages
    
    def process(self, items: List[T]) -> List[T]:
        """Process through pipeline"""
        result = items
        
        for stage in self.stages:
            if asyncio.iscoroutinefunction(stage):
                # Would need async handling
                result = [stage(item) for item in result]
            else:
                result = [stage(item) for item in result]
        
        return result
    
    def process_batch(self, items: List[T], batch_size: int = 100) -> List[T]:
        """Process in batches"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            results.extend(self.process(batch))
        
        return results


# Global processor
_processor: Optional[DistributedProcessor] = None


def get_processor(num_workers: int = 4) -> DistributedProcessor:
    """Get distributed processor"""
    global _processor
    if _processor is None:
        _processor = DistributedProcessor(num_workers)
    return _processor
