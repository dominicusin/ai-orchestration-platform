"""Task graph for distributed load balancing"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("orchestration.task_graph")


class TaskStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Task node in graph"""
    id: str
    name: str
    handler: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    dependencies: set[str] = field(default_factory=set)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    priority: int = 0

    def __hash__(self):
        return hash(self.id)


class TaskGraph:
    """Directed acyclic graph of tasks"""

    def __init__(self, name: str = "graph"):
        self.name = name
        self.tasks: dict[str, Task] = {}
        self.adjacency: dict[str, set[str]] = defaultdict(set)  # task -> dependent tasks
        self.reverse_adj: dict[str, set[str]] = defaultdict(set)  # task -> dependencies

    def add_task(self, task: Task):
        """Add task to graph"""
        self.tasks[task.id] = task
        self.adjacency[task.id] = set()
        self.reverse_adj[task.id] = set()

    def add_dependency(self, task_id: str, depends_on: str):
        """Add dependency: task_id depends on depends_on"""
        if task_id not in self.tasks or depends_on not in self.tasks:
            return

        self.tasks[task_id].dependencies.add(depends_on)
        self.adjacency[depends_on].add(task_id)
        self.reverse_adj[task_id].add(depends_on)

    def get_ready_tasks(self) -> list[Task]:
        """Get tasks with all dependencies satisfied"""
        ready = []

        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue

            # Check if all dependencies are completed
            deps_satisfied = all(
                self.tasks[dep].status == TaskStatus.COMPLETED
                for dep in task.dependencies
            )

            if deps_satisfied:
                task.status = TaskStatus.READY
                ready.append(task)

        return ready

    def get_execution_order(self) -> list[list[Task]]:
        """Get topological sort - layers of tasks that can run in parallel"""
        in_degree = {tid: len(deps) for tid, deps in self.reverse_adj.items()}
        layers = []
        remaining = set(self.tasks.keys())

        while remaining:
            # Find tasks with no pending dependencies
            ready = [
                tid for tid in remaining
                if in_degree.get(tid, 0) == 0
            ]

            if not ready:
                break  # Cycle detected

            layer = [self.tasks[tid] for tid in ready]
            layers.append(layer)

            # Update in-degrees
            for tid in ready:
                remaining.remove(tid)
                for dependent in self.adjacency[tid]:
                    in_degree[dependent] -= 1

        return layers

    def is_complete(self) -> bool:
        """Check if all tasks completed"""
        return all(
            task.status == TaskStatus.COMPLETED
            for task in self.tasks.values()
        )

    def has_failures(self) -> bool:
        """Check if any task failed"""
        return any(
            task.status == TaskStatus.FAILED
            for task in self.tasks.values()
        )


class TaskSplitter:
    """Split large tasks into smaller subtasks"""

    @staticmethod
    def split_by_files(files: list[str], batch_size: int = 10) -> list[list[str]]:
        """Split file list into batches"""
        return [files[i:i+batch_size] for i in range(0, len(files), batch_size)]

    @staticmethod
    def split_by_classes(classes: list[dict], parallelism: int = 4) -> list[list[dict]]:
        """Split classes into parallel groups"""
        groups = [[] for _ in range(parallelism)]

        for i, cls in enumerate(classes):
            groups[i % parallelism].append(cls)

        return [g for g in groups if g]

    @staticmethod
    def create_task_graph(
        items: list[Any],
        task_name: str,
        handler: Callable,
        batch_size: int = 10,
    ) -> TaskGraph:
        """Create task graph from items"""
        graph = TaskGraph(task_name)

        # Create batch tasks
        batches = TaskSplitter.split_by_files(items, batch_size)

        prev_task_id = None

        for i, batch in enumerate(batches):
            task_id = f"{task_name}_batch_{i}"

            task = Task(
                id=task_id,
                name=task_id,
                handler=handler,
                args=(batch,),
            )

            graph.add_task(task)

            # Add dependency on previous batch
            if prev_task_id:
                graph.add_dependency(task_id, prev_task_id)

            prev_task_id = task_id

        return graph


class DistributedExecutor:
    """Execute task graph across workers"""

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.workers: dict[int, asyncio.Queue] = {}
        self.results: dict[str, Any] = {}

    async def execute(self, graph: TaskGraph) -> dict[str, Any]:
        """Execute graph"""
        # Create worker queues
        for i in range(self.num_workers):
            self.workers[i] = asyncio.Queue()

        # Start workers
        worker_tasks = [
            asyncio.create_task(self._worker(i))
            for i in range(self.num_workers)
        ]

        # Submit ready tasks
        while not graph.is_complete():
            if graph.has_failures():
                break

            ready = graph.get_ready_tasks()

            if not ready:
                await asyncio.sleep(0.1)
                continue

            # Distribute tasks to workers
            for task in ready:
                worker_id = hash(task.id) % self.num_workers
                await self.workers[worker_id].put(task)

            await asyncio.sleep(0.1)

        # Wait for workers to finish
        for queue in self.workers.values():
            while not queue.empty():
                await queue.get()

        # Cancel worker tasks
        for wt in worker_tasks:
            wt.cancel()

        return self.results

    async def _worker(self, worker_id: int):
        """Worker coroutine"""
        queue = self.workers[worker_id]

        while True:
            try:
                task = await asyncio.wait_for(queue.get(), timeout=1.0)
            except TimeoutError:
                continue

            task.status = TaskStatus.RUNNING

            try:
                if asyncio.iscoroutinefunction(task.handler):
                    result = await task.handler(*task.args, **task.kwargs)
                else:
                    result = task.handler(*task.args, **task.kwargs)

                task.status = TaskStatus.COMPLETED
                task.result = result
                self.results[task.id] = result

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                logger.error(f"Task {task.id} failed: {e}")

            queue.task_done()


class LoadBalancer:
    """Distribute load across workers"""

    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.worker_loads: dict[int, int] = defaultdict(int)
        self.current = 0

    def select_worker(self, workers: list[int]) -> int:
        """Select worker based on strategy"""
        if self.strategy == "round_robin":
            worker = self.current % len(workers)
            self.current += 1
            return workers[worker]

        elif self.strategy == "least_loaded":
            return min(workers, key=lambda w: self.worker_loads[w])

        elif self.strategy == "random":
            import random
            return random.choice(workers)

        return workers[0]

    def record_completion(self, worker_id: int):
        """Record task completion"""
        self.worker_loads[worker_id] = max(0, self.worker_loads[worker_id] - 1)

    def record_start(self, worker_id: int):
        """Record task start"""
        self.worker_loads[worker_id] += 1


# Global executor
_executor: DistributedExecutor | None = None


def get_executor(num_workers: int = 4) -> DistributedExecutor:
    """Get distributed executor"""
    global _executor
    if _executor is None:
        _executor = DistributedExecutor(num_workers)
    return _executor
