"""Distributed job execution with graph-based task distribution"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("orchestration.jobs")


class JobStatus(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Distributed job"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: JobStatus = JobStatus.CREATED
    dependencies: set[str] = field(default_factory=set)
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    started_at: float = 0
    finished_at: float = 0

    @property
    def duration(self) -> float:
        if self.started_at > 0:
            end = self.finished_at or time.time()
            return end - self.started_at
        return 0


@dataclass
class JobResult:
    """Job execution result"""
    job_id: str
    success: bool
    result: Any = None
    error: str | None = None
    duration: float = 0


class JobGraph:
    """Graph of interdependent jobs"""

    def __init__(self):
        self.jobs: dict[str, Job] = {}
        self.edges: dict[str, set[str]] = defaultdict(set)
        self.reverse_edges: dict[str, set[str]] = defaultdict(set)

    def add_job(self, job: Job):
        """Add job to graph"""
        self.jobs[job.id] = job
        self.edges[job.id] = set()
        self.reverse_edges[job.id] = set()

    def add_dependency(self, job_id: str, depends_on: str):
        """job_id depends on depends_on"""
        if job_id not in self.jobs or depends_on not in self.jobs:
            return

        self.jobs[job_id].dependencies.add(depends_on)
        self.edges[depends_on].add(job_id)
        self.reverse_edges[job_id].add(depends_on)

    def get_ready_jobs(self) -> list[Job]:
        """Get jobs ready to execute"""
        ready = []

        for job in self.jobs.values():
            if job.status != JobStatus.CREATED:
                continue

            deps_met = all(
                self.jobs[d].status == JobStatus.COMPLETED
                for d in job.dependencies
            )

            if deps_met:
                ready.append(job)

        return ready

    def get_execution_layers(self) -> list[list[Job]]:
        """Get parallel execution layers"""
        in_degree = {jid: len(j.dependencies) for jid, j in self.jobs.items()}
        layers = []
        remaining = set(self.jobs.keys())

        while remaining:
            layer = [
                self.jobs[jid] for jid in remaining
                if in_degree.get(jid, 0) == 0
            ]

            if not layer:
                break

            layers.append(layer)

            for job in layer:
                remaining.discard(job.id)
                for dependent in self.edges[job.id]:
                    in_degree[dependent] -= 1

        return layers

    def is_complete(self) -> bool:
        """Check if all jobs done"""
        return all(
            j.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
            for j in self.jobs.values()
        )

    def has_failures(self) -> bool:
        """Check for failed jobs"""
        return any(j.status == JobStatus.FAILED for j in self.jobs.values())


class JobSplitter:
    """Split large jobs into subtasks"""

    @staticmethod
    def split_items(
        items: list[Any],
        num_chunks: int,
    ) -> list[list[Any]]:
        """Split items into chunks"""
        chunk_size = max(1, len(items) // num_chunks)
        return [items[i:i+chunk_size] for i in range(0, len(items), chunk_size)]

    @staticmethod
    def split_by_weight(
        items: list[dict],
        weights: dict[str, float],
    ) -> dict[str, list]:
        """Split by weight/processing time"""
        result = defaultdict(list)

        for item in items:
            key = item.get("key", "default")
            result[key].append(item)

        return dict(result)

    @staticmethod
    def create_job_dag(
        name: str,
        items: list[Any],
        processor: Callable,
        parallelism: int = 4,
    ) -> JobGraph:
        """Create DAG from items"""
        graph = JobGraph()

        # Split items
        chunks = JobSplitter.split_items(items, parallelism)

        # Create jobs for each chunk
        for i, chunk in enumerate(chunks):
            job = Job(
                id=f"{name}_chunk_{i}",
                name=f"chunk_{i}",
                func=processor,
                args=(chunk,),
            )
            graph.add_job(job)

        # Create aggregator job
        aggregator = Job(
            id=f"{name}_aggregator",
            name="aggregator",
            func=lambda results: results,
            args=([graph.jobs[f"{name}_chunk_{i}"].result for i in range(len(chunks))],),
        )

        # Add dependencies
        for i in range(len(chunks)):
            graph.add_dependency(
                f"{name}_aggregator",
                f"{name}_chunk_{i}",
            )

        graph.add_job(aggregator)

        return graph


class JobExecutor:
    """Execute job graph"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results: dict[str, JobResult] = {}

    async def execute(self, graph: JobGraph) -> dict[str, JobResult]:
        """Execute job graph"""
        # Get execution order
        layers = graph.get_execution_layers()

        # Process layer by layer
        for layer in layers:
            # Execute all jobs in layer concurrently
            tasks = [
                self._execute_job(job)
                for job in layer
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

            # Check for failures
            if graph.has_failures():
                logger.warning("Job execution failed, stopping")
                break

        return self.results

    async def _execute_job(self, job: Job):
        """Execute single job"""
        job.status = JobStatus.RUNNING
        job.started_at = time.time()

        try:
            if asyncio.iscoroutinefunction(job.func):
                result = await job.func(*job.args, **job.kwargs)
            else:
                result = job.func(*job.args, **job.kwargs)

            job.status = JobStatus.COMPLETED
            job.result = result
            job.finished_at = time.time()

            self.results[job.id] = JobResult(
                job_id=job.id,
                success=True,
                result=result,
                duration=job.duration,
            )

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.finished_at = time.time()

            self.results[job.id] = JobResult(
                job_id=job.id,
                success=False,
                error=str(e),
                duration=job.duration,
            )


class JobScheduler:
    """High-level job scheduler"""

    def __init__(self, num_workers: int = 4):
        self.executor = JobExecutor(num_workers)
        self.graphs: dict[str, JobGraph] = {}

    def submit(self, graph: JobGraph) -> str:
        """Submit job graph"""
        graph_id = str(uuid.uuid4())
        self.graphs[graph_id] = graph

        # Set all jobs to QUEUED
        for job in graph.jobs.values():
            job.status = JobStatus.QUEUED

        return graph_id

    async def run(self, graph_id: str) -> dict[str, JobResult]:
        """Run job graph"""
        graph = self.graphs.get(graph_id)
        if not graph:
            return {}

        return await self.executor.execute(graph)

    async def run_all(self) -> dict[str, dict[str, JobResult]]:
        """Run all submitted graphs"""
        results = {}

        for graph_id in self.graphs:
            results[graph_id] = await self.run(graph_id)

        return results


# Example: Process pipeline with DAG
class PipelineProcessor:
    """Process pipeline using DAG"""

    def __init__(self, num_workers: int = 4):
        self.scheduler = JobScheduler(num_workers)

    async def process(
        self,
        items: list[Any],
        stages: list[Callable],
    ) -> Any:
        """Process items through stages"""
        current = items

        for i, stage in enumerate(stages):
            # Create jobs for this stage
            graph = JobGraph()

            chunks = JobSplitter.split_items(current, self.max_workers)

            for j, chunk in enumerate(chunks):
                job = Job(
                    id=f"stage_{i}_chunk_{j}",
                    name=f"stage_{i}_chunk_{j}",
                    func=stage,
                    args=(chunk,),
                )
                graph.add_job(job)

            # Submit and run
            graph_id = self.scheduler.submit(graph)
            results = await self.scheduler.run(graph_id)

            # Collect results
            current = [
                r.result
                for r in results.values()
                if r.success and r.result
            ]
            current = [item for sublist in current for item in sublist]

        return current


# Global scheduler
_scheduler: JobScheduler | None = None


def get_job_scheduler(num_workers: int = 4) -> JobScheduler:
    """Get job scheduler"""
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler(num_workers)
    return _scheduler
