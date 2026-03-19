"""Templates for task generation"""

from typing import Dict, Any, List


TASK_TEMPLATE = {
    "id": "",
    "name": "",
    "type": "atomic",
    "handler": None,
    "capability": None,
    "dependencies": [],
    "args": [],
    "kwargs": {},
}


DAG_TEMPLATE = {
    "name": "",
    "version": "1.0",
    "tasks": {},
    "edges": [],
    "config": {
        "max_workers": 4,
        "timeout": 300,
    },
}


EXECUTION_RESULT_TEMPLATE = {
    "execution_id": "",
    "status": "pending",
    "started_at": "",
    "completed_at": "",
    "tasks": {},
    "layers": [],
    "metrics": {},
}


def create_task(name: str, handler, capability: str = None) -> Dict[str, Any]:
    """Create task from template"""
    task = TASK_TEMPLATE.copy()
    task["id"] = name
    task["name"] = name
    task["handler"] = handler
    task["capability"] = capability
    return task


def create_dag(name: str) -> Dict[str, Any]:
    """Create DAG from template"""
    dag = DAG_TEMPLATE.copy()
    dag["name"] = name
    return dag