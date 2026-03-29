"""Diff for DAG comparisons"""

import logging
from typing import Any

logger = logging.getLogger("orchestration.diff")


class DAGDiff:
    """Compare DAG structures"""

    def __init__(self):
        self.added: set[str] = set()
        self.removed: set[str] = set()
        self.modified: set[str] = set()
        self.unchanged: set[str] = set()

    def diff(self, old: dict[str, Any], new: dict[str, Any]) -> "DAGDiff":
        """Compute diff between two DAGs"""
        old_tasks = set(old.get("tasks", {}).keys())
        new_tasks = set(new.get("tasks", {}).keys())

        self.added = new_tasks - old_tasks
        self.removed = old_tasks - new_tasks

        common = old_tasks & new_tasks
        for task_id in common:
            if old["tasks"][task_id] != new["tasks"][task_id]:
                self.modified.add(task_id)
            else:
                self.unchanged.add(task_id)

        return self

    def to_dict(self) -> dict:
        return {
            "added": list(self.added),
            "removed": list(self.removed),
            "modified": list(self.modified),
            "unchanged": list(self.unchanged),
        }


class TaskDiff:
    """Compare task configurations"""

    @staticmethod
    def diff_tasks(old: dict, new: dict) -> dict[str, Any]:
        """Diff two tasks"""
        changes = {}

        for key in set(old.keys()) | set(new.keys()):
            if key not in old:
                changes[key] = {"type": "added", "value": new[key]}
            elif key not in new:
                changes[key] = {"type": "removed", "value": old[key]}
            elif old[key] != new[key]:
                changes[key] = {"type": "modified", "old": old[key], "new": new[key]}

        return changes


def diff_dags(dag1: dict, dag2: dict) -> dict:
    """Diff two DAGs"""
    diff = DAGDiff()
    return diff.diff(dag1, dag2).to_dict()
