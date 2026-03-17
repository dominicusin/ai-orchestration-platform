"""Execution engine for recursive DAG with agent assignment"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import time
import uuid

logger = logging.getLogger("orchestration.graph_engine")


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration: float = 0
    agent_id: Optional[str] = None


@dataclass
class Agent:
    """Worker agent"""
    id: str
    name: str
    capabilities: set
    busy: bool = False
    
    def can_execute(self, required_cap: str) -> bool:
        return required_cap in self.capabilities


class AgentPool:
    """Pool of execution agents"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
    
    def add_agent(self, agent: Agent):
        self.agents[agent.id] = agent
    
    def get_available(self, required_cap: str = None) -> Optional[Agent]:
        """Get available agent that can execute task"""
        for agent in self.agents.values():
            if not agent.busy:
                if required_cap is None or agent.can_execute(required_cap):
                    return agent
        return None
    
    def get_by_capability(self, required_cap: str) -> List[Agent]:
        """Get all agents with capability"""
        return [
            a for a in self.agents.values()
            if a.can_execute(required_cap)
        ]


class DAGExecutor:
    """Execute DAG with agent assignment"""
    
    def __init__(self, agent_pool: AgentPool):
        self.agent_pool = agent_pool
        self.results: Dict[str, ExecutionResult] = {}
        self.task_queue: asyncio.Queue = None
        self.workers: List[asyncio.Task] = []
    
    async def execute(self, dag) -> Dict[str, ExecutionResult]:
        """Execute DAG with topological ordering"""
        layers = dag.get_execution_layers()
        
        logger.info(f"Executing DAG with {len(layers)} layers")
        
        for layer_idx, layer in enumerate(layers):
            logger.info(f"Layer {layer_idx + 1}/{len(layers)}: {len(layer)} tasks")
            
            # Execute all tasks in layer concurrently
            tasks = []
            for task in layer:
                t = asyncio.create_task(self._execute_task(task))
                tasks.append(t)
            
            # Wait for layer to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for failures
            failed = [t for t in layer if self.results.get(t.id, ExecutionResult("", False)).success == False]
            if failed:
                logger.warning(f"Layer {layer_idx} has {len(failed)} failed tasks")
                break
        
        return self.results
    
    async def _execute_task(self, task) -> ExecutionResult:
        """Execute single task with agent"""
        start_time = time.time()
        
        # Get capable agent
        required_cap = task.required_capability.value if task.required_capability else None
        agent = self.agent_pool.get_available(required_cap)
        
        if agent is None:
            # Wait for available agent
            while agent is None:
                await asyncio.sleep(0.1)
                agent = self.agent_pool.get_available(required_cap)
        
        agent.busy = True
        
        try:
            # Execute task
            if task.handler:
                if asyncio.iscoroutinefunction(task.handler):
                    result = await task.handler(*task.args, **task.kwargs)
                else:
                    result = task.handler(*task.args, **task.kwargs)
            else:
                # Composite task - aggregate subtask results
                subtask_results = [
                    self.results[st.id].result
                    for st in task.subtasks
                    if st.id in self.results
                ]
                result = task.aggregator(subtask_results) if task.aggregator else subtask_results
            
            execution_result = ExecutionResult(
                task_id=task.id,
                success=True,
                result=result,
                duration=time.time() - start_time,
                agent_id=agent.id,
            )
            
        except Exception as e:
            execution_result = ExecutionResult(
                task_id=task.id,
                success=False,
                error=str(e),
                duration=time.time() - start_time,
                agent_id=agent.id,
            )
            logger.error(f"Task {task.id} failed: {e}")
        
        finally:
            agent.busy = False
        
        self.results[task.id] = execution_result
        return execution_result


class RecursiveExecutor:
    """Execute with recursive decomposition on-the-fly"""
    
    def __init__(self, agent_pool: AgentPool, max_depth: int = 5):
        self.agent_pool = agent_pool
        self.max_depth = max_depth
        self.results: Dict[str, Any] = {}
    
    async def execute(
        self,
        task_name: str,
        items: List[Any],
        decompose_func: Callable,
        process_func: Callable,
        depth: int = 0,
    ) -> Any:
        """
        Recursively execute with decomposition
        
        Returns when task is atomic (executable by agent)
        """
        # Check if should decompose
        should_decompose = depth < self.max_depth and len(items) > 10
        
        if not should_decompose:
            # Atomic - execute directly
            return await self._execute_atomic(task_name, items, process_func)
        
        # Decompose
        sub_groups = decompose_func(items)
        
        # Execute subtasks recursively
        subtask_results = {}
        for sub_name, sub_items in sub_groups.items():
            result = await self.execute(
                f"{task_name}.{sub_name}",
                sub_items,
                decompose_func,
                process_func,
                depth + 1,
            )
            subtask_results[sub_name] = result
        
        # Aggregate results
        return self._aggregate(subtask_results)
    
    async def _execute_atomic(
        self,
        task_name: str,
        items: List[Any],
        process_func: Callable,
    ) -> Any:
        """Execute atomic task with available agent"""
        # Get any available agent
        agent = self.agent_pool.get_available()
        
        if agent is None:
            await asyncio.sleep(0.1)
            return await self._execute_atomic(task_name, items, process_func)
        
        agent.busy = True
        try:
            return process_func(items)
        finally:
            agent.busy = False
    
    def _aggregate(self, results: Dict[str, Any]) -> Any:
        """Aggregate subtask results"""
        # Flatten if single value
        if len(results) == 1:
            return list(results.values())[0]
        return results


# Example: Execute pipeline with DAG
async def execute_pipeline(
    items: List[Any],
    stages: List[Callable],
    num_agents: int = 4,
) -> Dict[str, ExecutionResult]:
    """Execute pipeline with DAG"""
    
    # Create agents
    agent_pool = AgentPool()
    for i in range(num_agents):
        agent_pool.add_agent(Agent(
            id=f"agent_{i}",
            name=f"Worker {i}",
            capabilities={"file_read", "file_write", "llm_call", "code_execute", "data_transform"},
        ))
    
    # Build DAG from stages
    from orchestration.graph_recursive import RecursiveDAG
    
    dag = RecursiveDAG()
    
    for i, stage in enumerate(stages):
        # Simple decomposition for example
        def make_decomposer(idx):
            return lambda items: {
                f"chunk_{j}": items[j:j+10]
                for j in range(0, len(items), 10)
            }
        
        dag.build_from_decomposition(
            task_id=f"stage_{i}",
            task_name=f"stage_{i}",
            items=items,
            decompose_func=make_decomposer(i),
            get_handler=lambda itms: lambda: [stage(itm) for itm in itms],
            get_capability=lambda itms: "code_execute",
        )
    
    # Execute
    executor = DAGExecutor(agent_pool)
    return await executor.execute(dag)


# Global executor
_executor: Optional[DAGExecutor] = None


def get_executor(agent_pool: AgentPool) -> DAGExecutor:
    """Get executor instance"""
    global _executor
    if _executor is None:
        _executor = DAGExecutor(agent_pool)
    return _executor
