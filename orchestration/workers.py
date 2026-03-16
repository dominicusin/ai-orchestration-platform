"""Pipeline workers"""

import asyncio
import logging
from typing import Dict, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger("orchestration.workers")


@dataclass
class WorkerTask:
    """Worker task"""
    id: str
    handler: Callable
    args: tuple = ()
    kwargs: dict = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


class Worker:
    """Base worker"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.running = False
    
    async def process(self, task: WorkerTask):
        """Process task"""
        raise NotImplementedError


class AsyncWorker(Worker):
    """Async worker"""
    
    def __init__(self, worker_id: str):
        super().__init__(worker_id)
        self.tasks = asyncio.Queue()
    
    async def process(self, task: WorkerTask):
        return await task.handler(*task.args, **task.kwargs)
    
    async def run(self):
        """Run worker"""
        self.running = True
        while self.running:
            task = await self.tasks.get()
            await self.process(task)


class WorkerPool:
    """Pool of workers"""
    
    def __init__(self, size: int = 4):
        self.size = size
        self.workers = []
    
    def create_workers(self):
        """Create workers"""
        for i in range(self.size):
            self.workers.append(AsyncWorker(f"worker-{i}"))
    
    async def submit(self, task: WorkerTask):
        """Submit task"""
        # Simple round-robin
        worker = self.workers[len(task.id) % self.size]
        await worker.tasks.put(task)
