```python
"""Recursive DAG with agent-aware atomic task detection

Pattern: P requires [A, B], A requires [A1, A2]
Graph: [A1, A2] -> A -> P ; [B] -> P

Recursion stops at atomic operation executable by specific agent.
"""

import asyncio
import logging
from typing import Dict, Any, List, Set, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

logger = logging.getLogger("orchestration.graph_recursive")


class TaskType(Enum):
    ATOMIC = "atomic"       # Leaf - executable by agent
    COMPOSITE = "composite" # Branch - requires decomposition


class AgentCapability(Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    LLM_CALL = "llm_call"
    CODE_EXECUTE = "code_execute"
    DATA_TRANSFORM = "data_transform"
    VALIDATE = "validate"
    FORMAT = "format"


@dataclass
class Agent:
    """Execution agent with specific capabilities"""
    id: str
    name: str
    capabilities: Set[AgentCapability]
    
    def can_execute(self, required_cap: AgentCapability) -> bool:
        return required_cap in self.capabilities


@dataclass
class Task:
    """Task node in DAG"""
    id: str
    name: str
    task_type: TaskType = TaskType.COMPOSITE
    
    # Atomic: executable by agent
    handler: Optional[Callable] = None
    required_capability: Optional[AgentCapability] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    
    # Composite: has subtasks
    subtasks: List["Task"] = field(default_factory=list)
    aggregator: Optional[Callable] = None
    
    # State
    result: Any = None
    status: str = "pending"  # pending, ready, running, completed, failed
    
    def is_atomic(self) -> bool:
        return self.task_type == TaskType.ATOMIC
    
    def can_be_executed_by(self, agent: Agent) -> bool:
        """Check if agent can execute this task"""
        if self.is_atomic() and self.required_capability:
            return agent.can_execute(self.required_capability)
        return True


class RecursiveDAG:
    """Recursive DAG builder - builds graph as task is decomposed"""
    
    def __init__(self):
        self.root: Optional[Task] = None
        self.all_tasks: Dict[str, Task] = {}
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # dep -> dependent
    
    def build_from_decomposition(
        self,
        task_id: str,
        task_name: str,
        items: List[Any],
        decompose_func: Callable[[List], Dict[str, List]],  # Returns {"subtask": [...]} 
        get_handler: Callable,  # Returns handler for atomic task
        get_capability: Callable,  # Returns required capability
    ) -> "Task":
        """
        Recursively build DAG
        
        Example: P requires {"A": [...], "B": [...]}
                 A requires {"A1": [...], "A2": [...]}
        
        Result: [A1, A2] -> A -> P ; [B] -> P
        """
        # Check if should be atomic (base case)
        is_atomic = self._is_atomic_decomposition(items, decompose_func)
        
        if is_atomic:
            # Create atomic task
            task = Task(
                id=task_id,
                name=task_name,
                task_type=TaskType.ATOMIC,
                handler=get_handler(items),
                required_capability=get_capability(items),
            )
            self.all_tasks[task_id] = task
            return task
        
        # Composite: decompose into subtasks
        subtask_groups = decompose_func(items)
        
        # Create subtasks
        subtasks = []
        for subtask_name, subtask_items in subtask_groups.items():
            subtask_id = f"{task_id}_{subtask_name}"
            subtask = self.build_from_decomposition(
                subtask_id,
                f"{task_name}.{subtask_name}",
                subtask_items,
                decompose_func,
                get_handler,
                get_capability,
            )
            subtasks.append(subtask)
        
        # Create current task (aggregator)
        task = Task(
            id=task_id,
            name=task_name,
            task_type=TaskType.COMPOSITE,
            subtasks=subtasks,
            aggregator=lambda results: results,
        )
        
        # Add edges: subtasks -> current task
        for subtask in subtasks:
            self.edges[subtask.id].add(task.id)
        
        self.all_tasks[task_id] = task
        return task
    
    def _is_atomic_decomposition(
        self,
        items: List[Any],
        decompose_func: Callable,
    ) -> bool:
        """Check if decomposition returns atomic result"""
        result = decompose_func(items)
        
        # If returns dict with list values that can't be further decomposed
        if isinstance(result, dict):
            # Check if any value is still decomposable
            for value in result.values():
                if isinstance(value, list) and len(value) > 1:
                    # Check if further decomposition would help
                    sub_result = decompose_func(value)
                    if isinstance(sub_result, dict) and len(sub_result) > 1:
                        return False
            return True
        
        return True
    
    def get_execution_layers(self) -> List[List[Task]]:
        """Get layers for parallel execution (topological sort)"""
        # Calculate in-degree
        in_degree = defaultdict(int)
        for task in self.all_tasks.values():
            in_degree[task.id] = 0
        
        for dep, dependents in self.edges.items():
            for d in dependents:
                in_degree[d] += 1
        
        layers = []
        processed = set()
        
        while len(processed) < len(self.all_tasks):
            # Find tasks with no pending dependencies
            current_layer = [
                self.all_tasks[tid] 
                for tid, deg in in_degree.items()
                if deg == 0 and tid not in processed
            ]
            
            if not current_layer:
                break
            
            layers.append(current_layer)
            
            for task in current_layer:
                processed.add(task.id)
                # Reduce in-degree for dependents
                for dependent_id in self.edges.get(task.id, []):
                    in_degree[dependent_id] -= 1
        
        return layers
    
    def visualize(self) -> str:
        """ASCII visualization of DAG"""
        lines = ["DAG Structure:", "=" * 40]
        
        layers = self.get_execution_layers()
        for i, layer in enumerate(layers):
            tasks = ", ".join(t.name for t in layer)
            lines.append(f"Layer {i}: {tasks}")
        
        lines.append("\nEdges:")
        for dep, dependents in self.edges.items():
            for d in dependents:
                lines.append(f"  {dep} -> {d}")
        
        return "\n".join(lines)


# Example: Process pipeline with proper DAG
class PipelineDAGBuilder:
    """Build DAG for pipeline processing"""
    
    def __init__(self):
        self.dag = RecursiveDAG()
    
    def build(
        self,
        items: List[Any],
        stages: List[Callable],
    ) -> RecursiveDAG:
        """Build DAG for multi-stage pipeline"""
        
        # Stage decomposition function
        def decompose_stage(stage_items, stage_idx):
            # Split items for parallel processing
            n_workers = 4
            chunk_size = max(1, len(stage_items) // n_workers)
            return {
                f"chunk_{i}": stage_items[i:i+chunk_size]
                for i in range(0, len(stage_items), chunk_size)
            }
        
        # Build recursively through stages
        current = items
        
        for i, stage in enumerate(stages):
            self.dag.build_from_decomposition(
                task_id=f"stage_{i}",
                task_name=f"stage_{i}",
                items=current,
                decompose_func=lambda items: decompose_stage(items, i),
                get_handler=lambda items: lambda: [stage(item) for item in items],
                get_capability=lambda items: AgentCapability.CODE_EXECUTE,
            )
            # Would need to track results through stages
        
        return self.dag


# Test example
def example():
    """Example: P = A + B, where A = A1 + A2"""
    
    # Define decomposition rules
    def decompose(task_name, items):
        if task_name == "P":
            return {"A": items[:len(items)//2], "B": items[len(items)//2:]}
        elif task_name == "A":
            return {"A1": items[:len(items)//2], "A2": items[len(items)//2:]}
        return {task_name: items}
    
    # Define handlers for atomic tasks
    def get_handler(task_name, items):
        return lambda: f"processed_{task_name}"
    
    # Define capabilities
    def get_capability(task_name):
        if task_name in ("A1", "A2"):
            return AgentCapability.DATA_TRANSFORM
        elif task_name == "B":
            return AgentCapability.VALIDATE
        return AgentCapability.CODE_EXECUTE
    
    # Build DAG
    dag = RecursiveDAG()
    items = list(range(100))
    
    dag.build_from_decomposition(
        task_id="P",
        task_name="P",
        items=items,
        decompose_func=lambda i: decompose("P", i),
        get_handler=lambda i: get_handler("P", i),
        get_capability=lambda i: get_capability("P"),
    )
    
    print(dag.visualize())
    
    # Get execution layers
    layers = dag.get_execution_layers()
    print("\nExecution order:")
    for i, layer in enumerate(layers):
        print(f"  Layer {i}: {[t.name for t in layer]}")


if __name__ == "__main__":
    example()
```