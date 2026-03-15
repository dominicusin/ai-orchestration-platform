"""Batch processor for parallel file processing"""

import asyncio
import logging
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import time

logger = logging.getLogger("orchestration.processing")


@dataclass
class BatchItem:
    """Элемент батча"""
    id: str
    data: Any
    priority: int = 0
    metadata: Dict[str, Any] = None
    
    def __lt__(self, other):
        return self.priority < other.priority


@dataclass
class BatchResult:
    """Результат обработки"""
    item_id: str
    success: bool
    result: Any = None
    error: str = None
    duration: float = 0


class BatchProcessor:
    """Параллельный батч процессор"""
    
    def __init__(
        self,
        max_concurrent: int = 4,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        self.results: List[BatchResult] = []
        self.start_time: float = 0
        self.end_time: float = 0
    
    async def process(
        self,
        items: List[BatchItem],
        processor: Callable[[BatchItem], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[BatchResult]:
        """Обработка батча"""
        self.start_time = time.time()
        self.results = []
        
        tasks = []
        for item in items:
            task = self._process_item(item, processor)
            tasks.append(task)
        
        # Process with progress
        completed = 0
        total = len(items)
        
        for coro in asyncio.as_completed(tasks):
            result = await coro
            self.results.append(result)
            completed += 1
            
            if progress_callback:
                progress_callback(completed, total)
            
            # Log progress
            if completed % 10 == 0:
                logger.info(f"Progress: {completed}/{total} ({100*completed//total}%)")
        
        self.end_time = time.time()
        return self.results
    
    async def _process_item(
        self,
        item: BatchItem,
        processor: Callable[[BatchItem], Any],
    ) -> BatchResult:
        """Обработка одного элемента"""
        async with self.semaphore:
            start = time.time()
            
            for attempt in range(self.max_retries + 1):
                try:
                    # Run processor (could be sync or async)
                    if asyncio.iscoroutinefunction(processor):
                        result = await processor(item)
                    else:
                        result = processor(item)
                    
                    return BatchResult(
                        item_id=item.id,
                        success=True,
                        result=result,
                        duration=time.time() - start,
                    )
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {item.id}: {e}")
                    
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                    else:
                        return BatchResult(
                            item_id=item.id,
                            success=False,
                            error=str(e),
                            duration=time.time() - start,
                        )
            
            return BatchResult(
                item_id=item.id,
                success=False,
                error="Max retries exceeded",
                duration=time.time() - start,
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику"""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        
        return {
            "total_items": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "duration_seconds": self.end_time - self.start_time,
            "avg_item_duration": sum(r.duration for r in self.results) / total if total > 0 else 0,
        }


class PriorityBatchProcessor(BatchProcessor):
    """Batched processor с приоритетами"""
    
    async def process_priority(
        self,
        items: List[BatchItem],
        processor: Callable[[BatchItem], Any],
    ) -> List[BatchResult]:
        """Обработка с учётом приоритетов"""
        # Sort by priority (highest first)
        sorted_items = sorted(items, reverse=True)
        
        return await self.process(sorted_items, processor)


class ChunkedProcessor:
    """Processor для больших файлов с чанками"""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
    
    def chunk_list(self, items: List[Any]) -> List[List[Any]]:
        """Разделение на чанки"""
        return [
            items[i:i + self.chunk_size]
            for i in range(0, len(items), self.chunk_size)
        ]
    
    async def process_chunks(
        self,
        items: List[Any],
        processor: Callable[[List[Any]], Any],
        chunk_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Any]:
        """Обработка чанками"""
        chunks = self.chunk_list(items)
        results = []
        
        for i, chunk in enumerate(chunks):
            result = await processor(chunk)
            results.extend(result if isinstance(result, list) else [result])
            
            if chunk_callback:
                chunk_callback(i + 1, len(chunks))
        
        return results


class RateLimitedProcessor:
    """Processor с rate limiting"""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call = 0
    
    async def call(self, func: Callable, *args, **kwargs):
        """Вызов с rate limiting"""
        import time
        
        # Wait if needed
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        
        self.last_call = time.time()
        
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)


# Demo
async def demo():
    """Демонстрация"""
    processor = BatchProcessor(max_concurrent=4)
    
    items = [
        BatchItem(id=f"item_{i}", data={"value": i}, priority=i % 3)
        for i in range(20)
    ]
    
    async def process(item: BatchItem):
        await asyncio.sleep(0.1)  # Simulate work
        return {"processed": item.data}
    
    results = await processor.process(items, process)
    
    stats = processor.get_stats()
    print(f"Processed: {stats['successful']}/{stats['total_items']}")
    print(f"Duration: {stats['duration_seconds']:.2f}s")


if __name__ == "__main__":
    asyncio.run(demo())
