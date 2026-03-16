"""Batch processing for large-scale conversions"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

logger = logging.getLogger("orchestration.processing")


@dataclass
class BatchJob:
    """Batch job"""
    id: str
    name: str
    files: List[str]
    options: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed
    progress: int = 0
    results: List[Dict] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class BatchResult:
    """Batch result"""
    job_id: str
    file: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0


class BatchProcessor:
    """Process files in batches"""
    
    def __init__(
        self,
        max_workers: int = 4,
        batch_size: int = 10,
    ):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.jobs: Dict[str, BatchJob] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def create_job(
        self,
        name: str,
        files: List[str],
        options: Dict[str, Any] = None,
    ) -> str:
        """Create a batch job"""
        import uuid
        
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        job = BatchJob(
            id=job_id,
            name=name,
            files=files,
            options=options or {},
            created_at=datetime.now().isoformat(),
        )
        
        self.jobs[job_id] = job
        
        logger.info(f"Created batch job: {job_id} ({len(files)} files)")
        
        return job_id
    
    async def run_job(
        self,
        job_id: str,
        processor: Callable,
    ) -> BatchJob:
        """Run a batch job"""
        job = self.jobs.get(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        job.status = "running"
        job.started_at = datetime.now().isoformat()
        
        # Split into batches
        batches = [
            job.files[i:i + self.batch_size]
            for i in range(0, len(job.files), self.batch_size)
        ]
        
        logger.info(f"Running job {job_id} in {len(batches)} batches")
        
        for batch_idx, batch in enumerate(batches):
            # Process batch
            tasks = []
            for file_path in batch:
                task = asyncio.create_task(
                    self._process_file(processor, file_path, job.options)
                )
                tasks.append((file_path, task))
            
            # Wait for batch
            for file_path, task in tasks:
                try:
                    result = await task
                    job.results.append(result)
                    
                    if result.success:
                        logger.debug(f"Processed: {file_path}")
                    else:
                        job.errors.append({
                            "file": file_path,
                            "error": result.error,
                        })
                        
                except Exception as e:
                    job.errors.append({
                        "file": file_path,
                        "error": str(e),
                    })
            
            # Update progress
            job.progress = int((batch_idx + 1) / len(batches) * 100)
        
        job.status = "completed"
        job.completed_at = datetime.now().isoformat()
        
        logger.info(f"Job {job_id} completed: {len(job.results)} results, {len(job.errors)} errors")
        
        return job
    
    async def _process_file(
        self,
        processor: Callable,
        file_path: str,
        options: Dict[str, Any],
    ) -> BatchResult:
        """Process a single file"""
        import time
        
        start = time.time()
        
        try:
            # Run processor
            if asyncio.iscoroutinefunction(processor):
                output = await processor(file_path, options)
            else:
                output = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: processor(file_path, options)
                )
            
            return BatchResult(
                job_id="",
                file=file_path,
                success=True,
                output=output,
                duration=time.time() - start,
            )
            
        except Exception as e:
            return BatchResult(
                job_id="",
                file=file_path,
                success=False,
                error=str(e),
                duration=time.time() - start,
            )
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job status"""
        return self.jobs.get(job_id)
    
    def list_jobs(self, status: str = None) -> List[BatchJob]:
        """List jobs"""
        if status:
            return [j for j in self.jobs.values() if j.status == status]
        return list(self.jobs.values())
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.jobs.get(job_id)
        
        if job and job.status == "running":
            job.status = "cancelled"
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        total = len(self.jobs)
        completed = sum(1 for j in self.jobs.values() if j.status == "completed")
        failed = sum(1 for j in self.jobs.values() if j.status == "failed")
        running = sum(1 for j in self.jobs.values() if j.status == "running")
        
        return {
            "total_jobs": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "max_workers": self.max_workers,
            "batch_size": self.batch_size,
        }


class ChunkProcessor:
    """Process large files in chunks"""
    
    def __init__(self, chunk_size: int = 10000):
        self.chunk_size = chunk_size
    
    def process_file(
        self,
        file_path: str,
        processor: Callable,
        output_path: str = None,
    ) -> str:
        """Process file in chunks"""
        path = Path(file_path)
        content = path.read_text()
        
        # Split into chunks
        chunks = [
            content[i:i + self.chunk_size]
            for i in range(0, len(content), self.chunk_size)
        ]
        
        results = []
        
        for i, chunk in enumerate(chunks):
            result = processor(chunk, chunk_idx=i)
            results.append(result)
        
        # Combine results
        output = "\n".join(str(r) for r in results)
        
        if output_path:
            Path(output_path).write_text(output)
        
        return output
    
    def process_stream(
        self,
        input_path: str,
        processor: Callable,
        output_path: str,
    ):
        """Process file as stream"""
        path = Path(input_path)
        output = Path(output_path)
        
        with path.open("r") as infile, output.open("w") as outfile:
            chunk_idx = 0
            
            while True:
                chunk = infile.read(self.chunk_size)
                
                if not chunk:
                    break
                
                result = processor(chunk, chunk_idx=chunk_idx)
                outfile.write(str(result))
                
                chunk_idx += 1


class ParallelProcessor:
    """Parallel file processing"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    async def process_files(
        self,
        files: List[str],
        processor: Callable,
        options: Dict[str, Any] = None,
    ) -> List[BatchResult]:
        """Process files in parallel"""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_with_limit(file_path: str):
            async with semaphore:
                return await self._process(processor, file_path, options or {})
        
        tasks = [process_with_limit(f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        batch_results = []
        for file_path, result in zip(files, results):
            if isinstance(result, Exception):
                batch_results.append(BatchResult(
                    job_id="",
                    file=file_path,
                    success=False,
                    error=str(result),
                ))
            else:
                batch_results.append(result)
        
        return batch_results
    
    async def _process(
        self,
        processor: Callable,
        file_path: str,
        options: Dict[str, Any],
    ) -> BatchResult:
        """Process single file"""
        import time
        
        start = time.time()
        
        try:
            if asyncio.iscoroutinefunction(processor):
                output = await processor(file_path, options)
            else:
                output = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: processor(file_path, options)
                )
            
            return BatchResult(
                job_id="",
                file=file_path,
                success=True,
                output=output,
                duration=time.time() - start,
            )
            
        except Exception as e:
            return BatchResult(
                job_id="",
                file=file_path,
                success=False,
                error=str(e),
                duration=time.time() - start,
            )


# Global batch processor
_batch_processor: Optional[BatchProcessor] = None


def get_batch_processor() -> BatchProcessor:
    """Get batch processor"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor