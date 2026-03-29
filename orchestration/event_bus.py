"""
Event bus for pub/sub messaging
Шина событий для pub/sub коммуникации
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("orchestration.events")


class EventPriority(Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10


@dataclass
class Event:
    """Событие"""
    event_type: str
    data: Any
    source: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: EventPriority = EventPriority.NORMAL
    metadata: dict = field(default_factory=dict)


class Subscriber:
    """Подписчик"""

    def __init__(
        self,
        handler: Callable,
        event_types: list[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ):
        self.handler = handler
        self.event_types = event_types or []
        self.priority = priority
        self._enabled = True

    def matches(self, event_type: str) -> bool:
        """Проверка соответствия типа события"""
        if not self.event_types:
            return True
        return event_type in self.event_types

    async def handle(self, event: Event) -> Any:
        """Обработка события"""
        if not self._enabled:
            return None

        try:
            if asyncio.iscoroutinefunction(self.handler):
                return await self.handler(event)
            return self.handler(event)
        except Exception as e:
            logger.error(f"Subscriber error: {e}")
            return None


class EventBus:
    """
    Шина событий с pub/sub
    """

    def __init__(self):
        self._subscribers: list[Subscriber] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._processor_task: asyncio.Task | None = None

    def subscribe(
        self,
        handler: Callable,
        event_types: list[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> Subscriber:
        """Подписка на события"""
        subscriber = Subscriber(handler, event_types, priority)
        self._subscribers.append(subscriber)
        # Sort by priority (highest first)
        self._subscribers.sort(key=lambda s: s.priority.value, reverse=True)
        logger.info(f"Subscribed to: {event_types or 'all'}")
        return subscriber

    def unsubscribe(self, subscriber: Subscriber):
        """Отписка"""
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    async def publish(self, event: Event):
        """Публикация события"""
        # Process immediately for sync subscribers
        for subscriber in self._subscribers:
            if subscriber.matches(event.event_type):
                await subscriber.handle(event)

    async def publish_async(self, event: Event):
        """Асинхронная публикация"""
        await self._event_queue.put(event)

    async def start(self):
        """Запуск обработчика"""
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")

    async def stop(self):
        """Остановка обработчика"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Event bus stopped")

    async def _process_events(self):
        """Обработка событий из очереди"""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                await self.publish(event)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event processing error: {e}")

    def get_subscriber_count(self) -> int:
        """Количество подписчиков"""
        return len(self._subscribers)


# Event types
class PipelineEvents:
    """События pipeline"""
    PHASE_STARTED = "pipeline.phase.started"
    PHASE_COMPLETED = "pipeline.phase.completed"
    PHASE_FAILED = "pipeline.phase.failed"
    TASK_STARTED = "pipeline.task.started"
    TASK_COMPLETED = "pipeline.task.completed"
    TASK_FAILED = "pipeline.task.failed"
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"


class CacheEvents:
    """События кэша"""
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    CACHE_INVALIDATED = "cache.invalidated"
    CACHE_CLEARED = "cache.cleared"


class IntegrationEvents:
    """События интеграций"""
    GITHUB_PUSH = "github.push"
    GITLAB_PUSH = "gitlab.push"
    SLACK_MESSAGE = "slack.message"
    JIRA_ISSUE_CREATED = "jira.issue.created"


# Singleton
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Получение event bus"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
