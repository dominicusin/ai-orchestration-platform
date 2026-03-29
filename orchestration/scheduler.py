"""Recursive task scheduler with DAG-based load distribution"""

import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("orchestration.scheduler")


class TaskState(StrEnum):
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class SubTask:
    """Atomic subtask"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: int = 0
    timeout: float = 300
    retries: int = 0
    max_retries: int = 3

    def __hash__(self):
        return hash(self.id)


@dataclass
class TaskNode:
    """Task node in DAG"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    dependencies: set[str] = field(default_factory=set)
    children: set[str] = field(default_factory=set)
    state: TaskState = TaskState.IDLE
    result: Any = None
    error: str | None = None
    start_time: float = 0
    end_time: float = 0

    @property
    def duration(self) -> float:
        if self.end_time > 0:
            return self.end_time - self.start_time
        return time.time() - self.start_time if self.start_time > 0 else 0


class RecursiveTaskGraph:
    """Recursive DAG for complex task decomposition"""

    def __init__(self, name: str = "recursive_dag"):
        self.name = name
        self.nodes: dict[str, TaskNode] = {}
        self.root_ids: set[str] = set()
        self.leaf_ids: set[str] = set()

    def add_node(self, node: TaskNode):
        """Add node to DAG"""
        self.nodes[node.id] = node

        if not node.dependencies:
            self.root_ids.add(node.id)

        # Update leaf nodes
        if not node.children:
            self.leaf_ids.add(node.id)
        elif node.id in self.leaf_ids:
            self.leaf_ids.discard(node.id)

    def add_edge(self, from_id: str, to_id: str):
        """Add directed edge (from depends on to)"""
        if from_id not in self.nodes or to_id not in self.nodes:
            return

        self.nodes[from_id].dependencies.add(to_id)
        self.nodes[to_id].children.add(from_id)

        # Update roots/leaves
        if from_id in self.root_ids:
            self.root_ids.discard(from_id)

        if not self.nodes[to_id].children:
            self.leaf_ids.add(to_id)
        if to_id in self.leaf_ids:
            self.leaf_ids.discard(to_id)

    def get_ready_nodes(self) -> list[TaskNode]:
        """Get nodes with all dependencies satisfied"""
        ready = []

        for nid in self.root_ids:
            node = self.nodes[nid]
            if node.state == TaskState.IDLE:
                ready.append(node)

        for _nid, node in self.nodes.items():
            if node.state != TaskState.IDLE:
                continue

            deps_done = all(
                self.nodes[d].state == TaskState.DONE
                for d in node.dependencies
            )

            if deps_done:
                ready.append(node)

        return ready

    def get_execution_layers(self) -> list[list[TaskNode]]:
        """Get parallel execution layers (topological)"""
        in_degree = defaultdict(int)
        for nid, node in self.nodes.items():
            in_degree[nid] = len(node.dependencies)

        layers = []
        processed = set()

        while len(processed) < len(self.nodes):
            # Find all nodes with zero in-degree
            current_layer = [
                self.nodes[nid] for nid, deg in in_degree.items()
                if deg == 0 and nid not in processed
            ]

            if not current_layer:
                break

            layers.append(current_layer)

            for node in current_layer:
                processed.add(node.id)
                for child_id in node.children:
                    in_degree[child_id] -= 1

        return layers

    def split_recursive(
        self,
        task_id: str,
        items: list[Any],
        splitter: Callable[[list], list[list]],
        func: Callable,
    ) -> list[TaskNode]:
        """Recursively split task into subtasks"""
        nodes = []

        if len(items) <= 10:
            # Base case: small enough to process directly
            node = TaskNode(
                id=task_id,
                name=task_id,
                func=func,
                args=(items,),
            )
            nodes.append(node)
            return nodes

        # Recursive case: split into chunks
        chunks = splitter(items)

        for i, chunk in enumerate(chunks):
            child_nodes = self.split_recursive(
                f"{task_id}_chunk_{i}",
                chunk,
                splitter,
                func,
            )

            for child in child_nodes:
                nodes.append(child)
                self.add_edge(child.id, task_id)

        return nodes


class TaskQueue:
    """Priority queue for tasks"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queue: list[TaskNode] = []
        self.pending: dict[str, TaskNode] = {}

    def enqueue(self, node: TaskNode):
        """Add task to queue"""
        node.state = TaskState.QUEUED
        self.queue.append(node)
        self.pending[node.id] = node
        self._heapify()

    def dequeue(self) -> TaskNode | None:
        """Get highest priority task"""
        if not self.queue:
            return None

        self._heapify()
        node = self.queue.pop(0)
        node.state = TaskState.RUNNING
        node.start_time = time.time()
        return node

    def _heapify(self):
        """Sort by priority"""
        self.queue.sort(key=lambda n: -n.priority)

    def complete(self, node_id: str, result: Any = None):
        """Mark task complete"""
        if node_id in self.pending:
            node = self.pending[node_id]
            node.state = TaskState.DONE
            node.result = result
            node.end_time = time.time()

    def fail(self, node_id: str, error: str):
        """Mark task failed"""
        if node_id in self.pending:
            node = self.pending[node_id]
            node.state = TaskState.FAILED
            node.error = error
            node.end_time = time.time()

    def is_empty(self) -> bool:
        return len(self.queue) == 0

    def size(self) -> int:
        return len(self.queue)


class WorkerPool:
    """Pool of workers for task execution"""

    def __init__(self, size: int = 4):
        self.size = size
        self.workers: dict[int, asyncio.Task] = {}
        self.queue = TaskQueue()
        self.results: dict[str, Any] = {}
        self.running = False

    async def start(self):
        """Start workers"""
        self.running = True

        for i in range(self.size):
            worker = asyncio.create_task(self._worker(i))
            self.workers[i] = worker

    async def stop(self):
        """Stop workers"""
        self.running = False

        for worker in self.workers.values():
            worker.cancel()

        await asyncio.gather(*self.workers.values(), return_exceptions=True)

    async def submit(self, node: TaskNode):
        """Submit task"""
        self.queue.enqueue(node)

    async def _worker(self, worker_id: int):
        """Worker coroutine"""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            node = self.queue.dequeue()

            if node is None:
                await asyncio.sleep(0.1)
                continue

            try:
                logger.info(f"Worker {worker_id} executing {node.id}")

                if asyncio.iscoroutinefunction(node.func):
                    result = await node.func(*node.args, **node.kwargs)
                else:
                    result = node.func(*node.args, **node.kwargs)

                self.queue.complete(node.id, result)
                self.results[node.id] = result

            except Exception as e:
                logger.error(f"Worker {worker_id} failed {node.id}: {e}")
                self.queue.fail(node.id, str(e))

        logger.info(f"Worker {worker_id} stopped")


class RecursiveScheduler:
    """Recursive task scheduler with DAG"""

    def __init__(self, num_workers: int = 4):
        self.graph = RecursiveTaskGraph()
        self.pool = WorkerPool(num_workers)

    async def schedule(self, func: Callable, items: list[Any], **kwargs) -> dict:
        """Schedule recursive task execution"""
        # Create root task
        root = TaskNode(
            id="root",
            name="root",
            func=func,
            args=(items,),
            **kwargs,
        )

        self.graph.add_node(root)

        # Get execution layers
        layers = self.graph.get_execution_layers()

        # Start worker pool
        await self.pool.start()

        # Execute layer by layer
        for layer in layers:
            # Submit all tasks in layer
            for node in layer:
                await self.pool.submit(node)

            # Wait for layer to complete
            while any(n.state != TaskState.DONE for n in layer):
                await asyncio.sleep(0.1)

        # Stop pool
        await self.pool.stop()

        return self.pool.results

    def create_pipeline(
        self,
        stages: list[Callable],
        items: list[Any],
    ) -> RecursiveTaskGraph:
        """Create pipeline DAG"""
        graph = RecursiveTaskGraph()

        prev_id = None

        for i, stage_func in enumerate(stages):
            node_id = f"stage_{i}"

            node = TaskNode(
                id=node_id,
                name=node_id,
                func=stage_func,
                args=(items,),
            )

            graph.add_node(node)

            if prev_id:
                graph.add_edge(node_id, prev_id)

            prev_id = node_id

        self.graph = graph
        return graph


# Global scheduler
_scheduler: RecursiveScheduler | None = None


def get_scheduler(num_workers: int = 4) -> RecursiveScheduler:
    """Get scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = RecursiveScheduler(num_workers)
    return _scheduler
