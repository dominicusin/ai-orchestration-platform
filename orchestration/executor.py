"""Pipeline executor with async support"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger("orchestration.executor")


@dataclass
class ExecutionResult:
    """Execution result"""
    success: bool
    step: str
    duration: float
    output: Any = None
    error: Optional[str] = None


class SequentialExecutor:
    """Execute steps sequentially"""
    
    async def execute(self, steps: List[Callable], context: Dict) -> List[ExecutionResult]:
        """Execute steps in sequence"""
        results = []
        
        for step in steps:
            import time
            start = time.time()
            
            try:
                if asyncio.iscoroutinefunction(step):
                    output = await step(context)
                else:
                    output = step(context)
                
                results.append(ExecutionResult(
                    success=True,
                    step=step.__name__,
                    duration=time.time() - start,
                    output=output,
                ))
                
            except Exception as e:
                results.append(ExecutionResult(
                    success=False,
                    step=step.__name__,
                    duration=time.time() - start,
                    error=str(e),
                ))
                
                # Stop on error
                break
        
        return results


class ParallelExecutor:
    """Execute steps in parallel"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    async def execute(self, steps: List[Callable], context: Dict) -> List[ExecutionResult]:
        """Execute steps in parallel"""
        import time
        
        async def run_step(step):
            start = time.time()
            try:
                if asyncio.iscoroutinefunction(step):
                    output = await step(context)
                else:
                    output = step(context)
                return ExecutionResult(
                    success=True,
                    step=step.__name__,
                    duration=time.time() - start,
                    output=output,
                )
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    step=step.__name__,
                    duration=time.time() - start,
                    error=str(e),
                )
        
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def limited_run(step):
            async with semaphore:
                return await run_step(step)
        
        tasks = [limited_run(s) for s in steps]
        return await asyncio.gather(*tasks)


class PipelineExecutor:
    """Main pipeline executor"""
    
    def __init__(self, executor_type: str = "sequential"):
        if executor_type == "parallel":
            self.executor = ParallelExecutor()
        else:
            self.executor = SequentialExecutor()
    
    async def run(self, steps: List[Callable], context: Dict) -> List[ExecutionResult]:
        """Run pipeline"""
        return await self.executor.execute(steps, context)
