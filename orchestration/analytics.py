"""Analytics for distributed task execution"""

import time
import logging
from typing import Dict, Any, List
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger("orchestration.analytics")


@dataclass
class TaskMetrics:
    """Metrics for a task"""
    task_id: str
    start_time: float
    end_time: float = 0
    worker_id: int = 0
    status: str = "pending"
    error: str = ""
    
    @property
    def duration(self) -> float:
        if self.end_time > 0:
            return self.end_time - self.start_time
        return time.time() - self.start_time


@dataclass
class WorkerMetrics:
    """Metrics for a worker"""
    worker_id: int
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_duration: float = 0
    avg_duration: float = 0
    
    @property
    def success_rate(self) -> float:
        total = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / total if total > 0 else 0


class ExecutionAnalytics:
    """Analytics for task execution"""
    
    def __init__(self):
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.worker_metrics: Dict[int, WorkerMetrics] = {}
        self.start_time = time.time()
    
    def record_task_start(self, task_id: str, worker_id: int = 0):
        """Record task start"""
        self.task_metrics[task_id] = TaskMetrics(
            task_id=task_id,
            start_time=time.time(),
            worker_id=worker_id,
            status="running",
        )
    
    def record_task_end(self, task_id: str, success: bool = True, error: str = ""):
        """Record task end"""
        if task_id in self.task_metrics:
            metric = self.task_metrics[task_id]
            metric.end_time = time.time()
            metric.status = "completed" if success else "failed"
            metric.error = error
            
            # Update worker metrics
            self._update_worker(metric.worker_id, success, metric.duration)
    
    def _update_worker(self, worker_id: int, success: bool, duration: float):
        """Update worker metrics"""
        if worker_id not in self.worker_metrics:
            self.worker_metrics[worker_id] = WorkerMetrics(worker_id)
        
        wm = self.worker_metrics[worker_id]
        
        if success:
            wm.tasks_completed += 1
        else:
            wm.tasks_failed += 1
        
        wm.total_duration += duration
        wm.avg_duration = wm.total_duration / (wm.tasks_completed + wm.tasks_failed)
    
    def get_summary(self) -> Dict:
        """Get analytics summary"""
        total_tasks = len(self.task_metrics)
        completed = sum(1 for m in self.task_metrics.values() if m.status == "completed")
        failed = sum(1 for m in self.task_metrics.values() if m.status == "failed")
        
        durations = [m.duration for m in self.task_metrics.values() if m.end_time > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        total_time = time.time() - self.start_time
        throughput = completed / total_time if total_time > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total_tasks if total_tasks > 0 else 0,
            "avg_duration": avg_duration,
            "total_time": total_time,
            "throughput": throughput,
            "workers": {
                wid: {
                    "completed": wm.tasks_completed,
                    "failed": wm.tasks_failed,
                    "avg_duration": wm.avg_duration,
                    "success_rate": wm.success_rate,
                }
                for wid, wm in self.worker_metrics.items()
            },
        }
    
    def get_worker_load(self) -> Dict[int, float]:
        """Get worker load distribution"""
        total_duration = sum(
            wm.total_duration for wm in self.worker_metrics.values()
        )
        
        if total_duration == 0:
            return {wid: 0 for wid in self.worker_metrics}
        
        return {
            wid: wm.total_duration / total_duration
            for wid, wm in self.worker_metrics.items()
        }
    
    def get_bottlenecks(self) -> List[Dict]:
        """Find bottlenecks"""
        bottlenecks = []
        
        # Find slow tasks
        durations = [m.duration for m in self.task_metrics.values() if m.end_time > 0]
        if durations:
            threshold = max(durations) * 0.8
            slow_tasks = [
                m for m in self.task_metrics.values()
                if m.end_time > 0 and m.duration > threshold
            ]
            
            for m in slow_tasks:
                bottlenecks.append({
                    "type": "slow_task",
                    "task_id": m.task_id,
                    "duration": m.duration,
                })
        
        return bottlenecks
    
    def export_json(self) -> str:
        """Export analytics as JSON"""
        import json
        return json.dumps(self.get_summary(), indent=2)


# Global analytics
_analytics: ExecutionAnalytics = None


def get_analytics() -> ExecutionAnalytics:
    """Get analytics instance"""
    global _analytics
    if _analytics is None:
        _analytics = ExecutionAnalytics()
    return _analytics
