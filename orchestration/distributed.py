"""
Multi-node processing utilities
Утилиты для распределённой обработки на нескольких узлах
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiohttp

logger = logging.getLogger("orchestration.distributed")


@dataclass
class NodeInfo:
    """Информация об узле"""
    node_id: str
    hostname: str
    ip_address: str
    port: int
    status: str = "online"
    capabilities: list[str] = field(default_factory=list)
    load: float = 0.0
    memory_mb: float = 0.0
    last_seen: str = ""


@dataclass
class Task:
    """Задача для распределённого выполнения"""
    task_id: str
    task_type: str
    payload: dict
    priority: int = 0
    timeout: float = 300.0
    created_at: str = ""
    assigned_to: str = ""


@dataclass
class TaskResult:
    """Результат выполнения задачи"""
    task_id: str
    node_id: str
    success: bool
    result: Any = None
    error: str = ""
    duration: float = 0.0


class NodeRegistry:
    """
    Реестр узлов для распределённой обработки
    """

    def __init__(self, node_id: str = None):
        self.node_id = node_id or os.getenv("NODE_ID", "node-1")
        self._nodes: dict[str, NodeInfo] = {}
        self._heartbeat_interval = 10  # seconds

    def register_node(self, node: NodeInfo):
        """Регистрация узла"""
        self._nodes[node.node_id] = node
        logger.info(f"Node registered: {node.node_id}")

    def unregister_node(self, node_id: str):
        """Удаление узла"""
        if node_id in self._nodes:
            del self._nodes[node_id]
            logger.info(f"Node unregistered: {node_id}")

    def get_node(self, node_id: str) -> NodeInfo | None:
        """Получение узла"""
        return self._nodes.get(node_id)

    def get_online_nodes(self) -> list[NodeInfo]:
        """Получение онлайн узлов"""
        return [n for n in self._nodes.values() if n.status == "online"]

    def get_best_node(self, capability: str = None) -> NodeInfo | None:
        """Получение лучшего узла по нагрузке"""
        online = self.get_online_nodes()
        if not online:
            return None

        if capability:
            online = [n for n in online if capability in n.capabilities]

        if not online:
            return None

        # Выбираем с наименьшей нагрузкой
        return min(online, key=lambda n: n.load)

    def update_node_status(self, node_id: str, status: str):
        """Обновление статуса узла"""
        if node_id in self._nodes:
            self._nodes[node_id].status = status
            self._nodes[node_id].last_seen = datetime.now().isoformat()

    def get_all_nodes(self) -> list[NodeInfo]:
        """Получение всех узлов"""
        return list(self._nodes.values())


class DistributedTaskQueue:
    """
    Распределённая очередь задач
    """

    def __init__(self, registry: NodeRegistry):
        self.registry = registry
        self._pending_tasks: dict[str, Task] = {}
        self._running_tasks: dict[str, Task] = {}
        self._completed_tasks: dict[str, TaskResult] = {}
        self._lock = asyncio.Lock()

    async def submit_task(self, task: Task) -> str:
        """Отправка задачи"""
        async with self._lock:
            task.created_at = datetime.now().isoformat()
            self._pending_tasks[task.task_id] = task
            logger.info(f"Task submitted: {task.task_id}")

        # Try to assign immediately
        await self._try_assign_task(task.task_id)

        return task.task_id

    async def _try_assign_task(self, task_id: str):
        """Попытка назначить задачу узлу"""
        async with self._lock:
            task = self._pending_tasks.get(task_id)
            if not task:
                return

            # Find best node
            node = self.registry.get_best_node()
            if not node:
                return

            # Assign to node
            task.assigned_to = node.node_id
            self._running_tasks[task_id] = task
            del self._pending_tasks[task_id]

            logger.info(f"Task {task_id} assigned to {node.node_id}")

    async def complete_task(self, result: TaskResult):
        """Завершение задачи"""
        async with self._lock:
            if result.task_id in self._running_tasks:
                del self._running_tasks[result.task_id]

            self._completed_tasks[result.task_id] = result
            logger.info(f"Task {result.task_id} completed: {result.success}")

    async def get_task_status(self, task_id: str) -> str:
        """Получение статуса задачи"""
        if task_id in self._pending_tasks:
            return "pending"
        if task_id in self._running_tasks:
            return "running"
        if task_id in self._completed_tasks:
            return "completed"
        return "unknown"

    def get_queue_stats(self) -> dict:
        """Получение статистики очереди"""
        return {
            "pending": len(self._pending_tasks),
            "running": len(self._running_tasks),
            "completed": len(self._completed_tasks),
            "online_nodes": len(self.registry.get_online_nodes()),
        }


class DistributedExecutor:
    """
    Распределённый исполнитель задач
    """

    def __init__(self, node_url: str = None):
        self.node_url = node_url or os.getenv("NODE_URL", "http://localhost:8080")
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение сессии"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def execute_on_node(
        self,
        node_url: str,
        task: Task,
    ) -> TaskResult:
        """Выполнение задачи на удалённом узле"""
        start_time = datetime.now()

        try:
            session = await self._get_session()
            async with session.post(
                f"{node_url}/api/v1/execute",
                json={
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "payload": task.payload,
                },
                timeout=aiohttp.ClientTimeout(total=task.timeout),
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return TaskResult(
                        task_id=task.task_id,
                        node_id=node_url,
                        success=True,
                        result=result,
                        duration=(datetime.now() - start_time).total_seconds(),
                    )
                else:
                    return TaskResult(
                        task_id=task.task_id,
                        node_id=node_url,
                        success=False,
                        error=f"HTTP {resp.status}",
                        duration=(datetime.now() - start_time).total_seconds(),
                    )
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                node_id=node_url,
                success=False,
                error=str(e),
                duration=(datetime.now() - start_time).total_seconds(),
            )

    async def execute_distributed(
        self,
        tasks: list[Task],
        nodes: list[str],
    ) -> list[TaskResult]:
        """Распределённое выполнение задач"""
        # Distribute tasks across nodes
        results = []
        for i, task in enumerate(tasks):
            node_url = nodes[i % len(nodes)]
            result = await self.execute_on_node(node_url, task)
            results.append(result)

        return results

    async def close(self):
        """Закрытие сессии"""
        if self._session and not self._session.closed:
            await self._session.close()


# Singleton
_node_registry: NodeRegistry | None = None
_task_queue: DistributedTaskQueue | None = None


def get_node_registry(node_id: str = None) -> NodeRegistry:
    """Получение реестра узлов"""
    global _node_registry
    if _node_registry is None:
        _node_registry = NodeRegistry(node_id)
    return _node_registry


def get_task_queue(registry: NodeRegistry = None) -> DistributedTaskQueue:
    """Получение очереди задач"""
    global _task_queue
    if _task_queue is None:
        registry = registry or get_node_registry()
        _task_queue = DistributedTaskQueue(registry)
    return _task_queue
