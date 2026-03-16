"""Job scheduler for background tasks"""

import os
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger("orchestration.jobs")


class JobStatus(Enum):
    """Job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Job:
    """Background job"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    status: str = JobStatus.PENDING.value
    priority: int = JobPriority.NORMAL.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class JobScheduler:
    """Background job scheduler"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.jobs: Dict[str, Job] = {}
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.queue: asyncio.PriorityQueue = None
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
    
    def _init_queue(self):
        """Initialize priority queue"""
        if self.queue is None:
            self.queue = asyncio.PriorityQueue()
    
    async def start(self):
        """Start scheduler"""
        if self._running:
            return
        
        self._init_queue()
        self._running = True
        
        # Start worker tasks
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        for i in range(self.max_workers):
            asyncio.create_task(self._worker_loop(i))
        
        logger.info(f"Job scheduler started with {self.max_workers} workers")
    
    async def stop(self):
        """Stop scheduler"""
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
        
        # Wait for running jobs
        for task in self.running_jobs.values():
            task.cancel()
        
        logger.info("Job scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._running:
            # Find pending jobs
            pending = [
                (job.priority, job.id, job)
                for job in self.jobs.values()
                if job.status == JobStatus.PENDING.value
            ]
            
            # Sort by priority
            pending.sort(key=lambda x: (x[0], x[2].created_at))
            
            # Add to queue
            for priority, job_id, job in pending[:self.max_workers]:
                await self.queue.put((priority, job_id))
                job.status = JobStatus.RUNNING.value
                job.started_at = datetime.now().isoformat()
            
            await asyncio.sleep(1)
    
    async def _worker_loop(self, worker_id: int):
        """Worker loop"""
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Get job from queue
                priority, job_id = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                job = self.jobs.get(job_id)
                
                if job:
                    await self._execute_job(job)
                
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
    
    async def _execute_job(self, job: Job):
        """Execute a job"""
        try:
            logger.info(f"Executing job: {job.name}")
            
            # Run job
            if asyncio.iscoroutinefunction(job.func):
                job.result = await job.func(*job.args, **job.kwargs)
            else:
                job.result = job.func(*job.args, **job.kwargs)
            
            # Mark completed
            job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.now().isoformat()
            
            logger.info(f"Job completed: {job.name}")
            
        except Exception as e:
            logger.error(f"Job failed: {job.name} - {e}")
            
            job.error = str(e)
            
            # Retry if possible
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = JobStatus.PENDING.value
            else:
                job.status = JobStatus.FAILED.value
                job.completed_at = datetime.now().isoformat()
        
        finally:
            if job.id in self.running_jobs:
                del self.running_jobs[job.id]
    
    def submit(
        self,
        name: str,
        func: Callable,
        *args,
        priority: int = JobPriority.NORMAL.value,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
        """Submit a job"""
        job_id = str(uuid.uuid4())[:8]
        
        job = Job(
            id=job_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
        )
        
        self.jobs[job_id] = job
        
        logger.info(f"Job submitted: {name} ({job_id})")
        
        return job_id
    
    def submit_async(self, name: str, func: Callable, *args, **kwargs) -> str:
        """Submit async job"""
        return self.submit(name, func, *args, **kwargs)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.jobs.get(job_id)
        
        if not job:
            return False
        
        if job.status == JobStatus.RUNNING.value:
            job.status = JobStatus.CANCELLED.value
            return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "running": self._running,
            "total_jobs": len(self.jobs),
            "pending": sum(1 for j in self.jobs.values() if j.status == JobStatus.PENDING.value),
            "running_count": sum(1 for j in self.jobs.values() if j.status == JobStatus.RUNNING.value),
            "completed": sum(1 for j in self.jobs.values() if j.status == JobStatus.COMPLETED.value),
            "failed": sum(1 for j in self.jobs.values() if j.status == JobStatus.FAILED.value),
            "workers": self.max_workers,
        }
    
    def list_jobs(self, status: str = None) -> List[Dict[str, Any]]:
        """List jobs"""
        jobs = self.jobs.values()
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        return [
            {
                "id": j.id,
                "name": j.name,
                "status": j.status,
                "priority": j.priority,
                "created_at": j.created_at,
                "started_at": j.started_at,
                "completed_at": j.completed_at,
                "error": j.error,
            }
            for j in jobs
        ]


# Global scheduler
_scheduler: Optional[JobScheduler] = None


def get_job_scheduler() -> JobScheduler:
    """Get global job scheduler"""
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler


# Convenience decorators
def schedule(priority: int = JobPriority.NORMAL.value, max_retries: int = 3):
    """Decorator to schedule a function"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            scheduler = get_job_scheduler()
            return scheduler.submit(
                func.__name__,
                func,
                *args,
                priority=priority,
                max_retries=max_retries,
                **kwargs,
            )
        return wrapper
    return decorator


from functools import wraps
