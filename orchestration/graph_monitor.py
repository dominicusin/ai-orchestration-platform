"""DAG execution monitoring and metrics"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger("orchestration.graph_monitor")


@dataclass
class TaskMetrics:
    """Metrics for a single task"""
    task_id: str
    task_name: str
    layer: int
    start_time: float
    end_time: float = 0
    status: str = "pending"  # pending, running, completed, failed
    agent_id: Optional[str] = None
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        if self.end_time > 0:
            return self.end_time - self.start_time
        return time.time() - self.start_time


@dataclass
class LayerMetrics:
    """Metrics for a layer"""
    layer_index: int
    task_count: int
    start_time: float
    end_time: float = 0
    completed: int = 0
    failed: int = 0
    
    @property
    def duration(self) -> float:
        if self.end_time > 0:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def success_rate(self) -> float:
        total = self.completed + self.failed
        return self.completed / total if total > 0 else 0


class DAGMonitor:
    """Monitor DAG execution"""
    
    def __init__(self):
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.layer_metrics: Dict[int, LayerMetrics] = {}
        self.execution_id: str = str(time.time())
        self.start_time = time.time()
    
    def task_started(self, task_id: str, task_name: str, layer: int, agent_id: str = None):
        """Record task start"""
        self.task_metrics[task_id] = TaskMetrics(
            task_id=task_id,
            task_name=task_name,
            layer=layer,
            start_time=time.time(),
            status="running",
            agent_id=agent_id,
        )
    
    def task_completed(self, task_id: str, result: Any = None):
        """Record task completion"""
        if task_id in self.task_metrics:
            m = self.task_metrics[task_id]
            m.end_time = time.time()
            m.status = "completed"
    
    def task_failed(self, task_id: str, error: str):
        """Record task failure"""
        if task_id in self.task_metrics:
            m = self.task_metrics[task_id]
            m.end_time = time.time()
            m.status = "failed"
            m.error = error
    
    def layer_started(self, layer_index: int, task_count: int):
        """Record layer start"""
        self.layer_metrics[layer_index] = LayerMetrics(
            layer_index=layer_index,
            task_count=task_count,
            start_time=time.time(),
        )
    
    def layer_completed(self, layer_index: int, completed: int, failed: int):
        """Record layer completion"""
        if layer_index in self.layer_metrics:
            m = self.layer_metrics[layer_index]
            m.end_time = time.time()
            m.completed = completed
            m.failed = failed
    
    def get_summary(self) -> Dict:
        """Get execution summary"""
        total_tasks = len(self.task_metrics)
        completed = sum(1 for m in self.task_metrics.values() if m.status == "completed")
        failed = sum(1 for m in self.task_metrics.values() if m.status == "failed")
        
        task_durations = [m.duration for m in self.task_metrics.values() if m.end_time > 0]
        avg_task_duration = sum(task_durations) / len(task_durations) if task_durations else 0
        
        total_duration = time.time() - self.start_time
        throughput = completed / total_duration if total_duration > 0 else 0
        
        # Worker load
        worker_load = defaultdict(int)
        for m in self.task_metrics.values():
            if m.agent_id:
                worker_load[m.agent_id] += 1
        
        return {
            "execution_id": self.execution_id,
            "total_duration": total_duration,
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total_tasks if total_tasks > 0 else 0,
            "avg_task_duration": avg_task_duration,
            "throughput": throughput,
            "layers": len(self.layer_metrics),
            "worker_load": dict(worker_load),
        }
    
    def get_layer_summary(self) -> List[Dict]:
        """Get per-layer summary"""
        return [
            {
                "layer": m.layer_index,
                "tasks": m.task_count,
                "completed": m.completed,
                "failed": m.failed,
                "duration": m.duration,
                "success_rate": m.success_rate,
            }
            for m in self.layer_metrics.values()
        ]
    
    def get_slowest_tasks(self, limit: int = 10) -> List[Dict]:
        """Get slowest tasks"""
        sorted_tasks = sorted(
            self.task_metrics.values(),
            key=lambda m: m.duration,
            reverse=True,
        )
        
        return [
            {
                "task_id": m.task_id,
                "task_name": m.task_name,
                "duration": m.duration,
                "status": m.status,
            }
            for m in sorted_tasks[:limit]
        ]
    
    def get_bottlenecks(self) -> List[Dict]:
        """Identify bottlenecks"""
        bottlenecks = []
        
        # Slow layers
        layer_durations = [(i, m.duration) for i, m in self.layer_metrics.items()]
        if layer_durations:
            max_duration = max(d for _, d in layer_durations)
            threshold = max_duration * 0.5
            
            for idx, dur in layer_durations:
                if dur > threshold:
                    bottlenecks.append({
                        "type": "slow_layer",
                        "layer": idx,
                        "duration": dur,
                    })
        
        # Failed tasks
        failed_tasks = [m for m in self.task_metrics.values() if m.status == "failed"]
        if failed_tasks:
            bottlenecks.append({
                "type": "failed_tasks",
                "count": len(failed_tasks),
                "task_ids": [m.task_id for m in failed_tasks],
            })
        
        return bottlenecks
    
    def export_json(self) -> str:
        """Export metrics as JSON"""
        import json
        return json.dumps({
            "summary": self.get_summary(),
            "layers": self.get_layer_summary(),
            "slowest_tasks": self.get_slowest_tasks(5),
            "bottlenecks": self.get_bottlenecks(),
        }, indent=2)


# Global monitor
_monitor: Optional[DAGMonitor] = None


def get_monitor() -> DAGMonitor:
    """Get monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = DAGMonitor()
    return _monitor


def reset_monitor():
    """Reset monitor"""
    global _monitor
    _monitor = DAGMonitor()
