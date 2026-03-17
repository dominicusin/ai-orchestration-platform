```python
"""Recursive DAG-based task execution with topological ordering

Task Graph Model:
    [A1, A2] -> A -> P
    [B]    -> P
    
Execution via topological sort to determine exact launch order.
Recursion stops at atomic operations executable by specific agents.
"""

import asyncio
import logging
from typing import Dict, Any, List, Set, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import uuid
import time

logger = logging.getLogger("orchestration.graph_integration")


class TaskType(str, Enum):
    """Task type"""
    ATOMIC = "atomic"       # Can be executed by specific agent
    COMPOSITE = "composite" # Requires decomposition
    PIPELINE = "pipeline"   # Sequential stages


class AgentCapability(str, Enum):
    """Agent capabilities"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    LLM_CALL = "llm_call"
    CODE_EXECUTE = "code_execute"
    DATA_TRANSFORM = "data_transform"
    VALIDATE = "validate"
    FORMAT = "format"


@dataclass
class Agent:
    """Execution agent with capabilities"""
    id: str
    name: str
    capabilities: Set[AgentCapability]
    available: bool = True
    
    def can_execute(self, task: "Task") -> bool:
        """Check if agent can execute task"""
        if task.required_capability is None:
            return True
        return task.required_capability in self.capabilities


@dataclass
class Task:
    """Task node in DAG"""
    id: str
    name: str
    task_type: TaskType = TaskType.COMPOSITE
    
    # For atomic tasks
    handler: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    required_capability: Optional[AgentCapability] = None
    
    # For composite tasks
    decomposer: Optional[Callable] = None
    subtasks: List["Task"] = field(default_factory=list)
    
    # Dependencies (edges pointing TO this task)
    dependencies: Set[str] = field(default_factory=set)
    
    # State
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    level: int = 0  # Depth in recursion tree
    
    def is_atomic(self) -> bool:
        """Check if task is atomic"""
        return self.task_type == TaskType.ATOMIC
    
    def can_execute(self, agent: Agent) -> bool:
        """Check if task can be executed"""
        if self.is_atomic() and self.required_capability:
            return self.required_capability in agent.capabilities
        return True


class TaskGraph:
    """Directed Acyclic Graph of tasks with topological ordering"""
    
    def __init__(self, name: str = "task_graph"):
        self.name = name
        self.tasks: Dict[str, Task] = {}
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # from -> {to}
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)  # to -> {from}
    
    def add_task(self, task: Task):
        """Add task to graph"""
        self.tasks[task.id] = task
        self.edges[task.id] = set()
        self.reverse_edges[task.id] = set()
    
    def add_edge(self, from_id: str, to_id: str):
        """Add directed edge: from_id -> to_id (from_id is dependency of to_id)"""
        if from_id not in self.tasks or to_id not in self.tasks:
            logger.warning(f"Cannot add edge: task not found")
            return
        
        self.edges[from_id].add(to_id)
        self.reverse_edges[to_id].add(from_id)
        self.tasks[to_id].dependencies.add(from_id)
    
    def topological_sort(self) -> List[List[Task]]:
        """Get execution order using Kahn's algorithm (layers of parallel tasks)"""
        # Calculate in-degree for each node
        in_degree = {tid: len(self.tasks[tid].dependencies) for tid in self.tasks}
        
        layers = []
        processed = set()
        
        while len(processed) < len(self.tasks):
            # Find all nodes with in-degree 0 (no dependencies)
            current_layer = [
                self.tasks[tid] for tid in self.tasks
                if in_degree.get(tid, 0) == 0 and tid not in processed
            ]
            
            if not current_layer:
                logger.error("Cycle detected in task graph!")
                break
            
            layers.append(current_layer)
            
            for task in current_layer:
                processed.add(task.id)
                # Reduce in-degree for all dependents
                for dependent_id in self.edges[task.id]:
                    in_degree[dependent_id] -= 1
        
        return layers
    
    def get_execution_order(self) -> List[Task]:
        """Flatten to single execution order"""
        layers = self.topological_sort()
        order = []
        for layer in layers:
            order.extend(layer)
        return order
    
    def visualize(self) -> str:
        """Visualize graph structure"""
        lines = [f"TaskGraph: {self.name}"]
        lines.append("=" * 40)
        
        for task_id, task in self.tasks.items():
            deps = list(task.dependencies)
            deps_str = ", ".join(deps) if deps else "(root)"
            lines.append(f"{task_id} [{task.task_type.value}] <- [{deps_str}]")
        
        return "\n".join(lines)


class RecursiveDecomposer:
    """Recursively decompose composite tasks into atomic tasks"""
    
    def __init__(self, min_chunk_size: int = 1, max_depth: int = 10):
        self.min_chunk_size = min_chunk_size
        self.max_depth = max_depth
    
    def decompose(
        self,
        task: Task,
        items: List[Any],
        depth: int = 0,
    ) -> TaskGraph:
        """Recursively decompose task into atomic subtasks"""
        graph = TaskGraph(f"graph_{task.id}")
        
        if depth >= self.max_depth or len(items) <= self.min_chunk_size:
            # Base case: create atomic task
            atomic = Task(
                id=f"{task.id}_atomic",
                name=f"{task.name}_atomic",
                task_type=TaskType.ATOMIC,
                handler=task.handler,
                args=(items,),
                kwargs=task.kwargs,
                required_capability=task.required_capability,
                level=depth,
            )
            graph.add_task(atomic)
            return graph
        
        # Recursive case: split into chunks
        chunks = self._split_items(items)
        
        # Create subtasks for each chunk
        subtasks = []
        for i, chunk in enumerate(chunks):
            subtask = Task(
                id=f"{task.id}_sub_{i}",
                name=f"{task.name}_sub_{i}",
                task_type=TaskType.COMPOSITE,
                decomposer=task.decomposer,
                level=depth + 1,
            )
            subtasks.append(subtask)
            graph.add_task(subtask)
        
        # Create aggregator task
        aggregator = Task(
            id=f"{task.id}_agg",
            name=f"{task.name}_agg",
            task_type=TaskType.ATOMIC,
            handler=lambda results: results,
            args=(subtasks,),
            level=depth + 1,
        )
        graph.add_task(aggregator)
        
        # Add edges: subtasks -> aggregator
        for subtask in subtasks:
            graph.add_edge(subtask.id, aggregator.id)
        
        return graph
    
    def _split_items(self, items: List[Any]) -> List[List[Any]]:
        """Split items into chunks"""
        if not items:
            return []
        
        n = len(items)
        if n <= self.min_chunk_size:
            return [items]
        
        # Split into 2 parts recursively
        mid = n // 2
        left = self._split_items(items[:mid])
        right = self._split_items(items[mid:])
        
        return left + right


class DAGExecutor:
    """Execute tasks in DAG order with agent assignment"""
    
    def __init__(self, agents: List[Agent]):
        self.agents = {a.id: a for a in agents}
        self.results: Dict[str, Any] = {}
        self.task_status: Dict[str, str] = {}
    
    def execute(self, graph: TaskGraph) -> Dict[str, Any]:
        """Execute all tasks in topological order"""
        layers = graph.topological_sort()
        
        for layer_idx, layer in enumerate(layers):
            logger.info(f"Executing layer {layer_idx + 1}/{len(layers)} with {len(layer)} tasks")
            
            # Execute all tasks in layer concurrently
            for task in layer:
                self._execute_task(task)
            
            # Wait for layer completion
            layer_done = all(
                self.task_status.get(t.id) in ("completed", "failed")
                for t in layer
            )
            
            # Check for failures
            if any(self.task_status.get(t.id) == "failed" for t in layer):
                logger.warning("Layer has failed tasks, stopping")
                break
        
        return self.results
    
    def _execute_task(self, task: Task):
        """Execute single task"""
        self.task_status[task.id] = "running"
        
        try:
            if task.handler:
                result = task.handler(*task.args, **task.kwargs)
            else:
                result = None
            
            self.results[task.id] = result
            self.task_status[task.id] = "completed"
            
        except Exception as e:
            self.task_status[task.id] = "failed"
            self.error_messages[task.id] = str(e)
            logger.error(f"Task {task.id} failed: {e}")


# Example usage
def create_pipeline_graph(items: List, stages: List[Callable]) -> TaskGraph:
    """Create pipeline DAG from stages"""
    graph = TaskGraph("pipeline")
    
    prev_task = None
    
    for i, stage in enumerate(stages):
        task = Task(
            id=f"stage_{i}",
            name=f"stage_{i}",
            task_type=TaskType.COMPOSITE,
            handler=stage,
            args=(items,),
        )
        
        graph.add_task(task)
        
        if prev_task:
            graph.add_edge(prev_task.id, task.id)
        
        prev_task = task
    
    return graph


# Global decomposer
_decomposer: Optional[RecursiveDecomposer] = None


def get_decomposer() -> RecursiveDecomposer:
    """Get decomposer instance"""
    global _decomposer
    if _decomposer is None:
        _decomposer = RecursiveDecomposer()
    return _decomposer
