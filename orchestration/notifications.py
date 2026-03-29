"""
Notification system
Система уведомлений
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("orchestration.notifications")


class NotificationLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    CONSOLE = "console"
    WEBHOOK = "webhook"


@dataclass
class Notification:
    """Уведомление"""
    level: NotificationLevel
    title: str
    message: str
    channel: NotificationChannel = NotificationChannel.CONSOLE
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)


class NotificationHandler:
    """Обработчик уведомлений"""

    def __init__(self, channel: NotificationChannel):
        self.channel = channel
        self._handlers: dict[NotificationChannel, Callable] = {}

    def register_handler(self, channel: NotificationChannel, handler: Callable):
        """Регистрация обработчика"""
        self._handlers[channel] = handler

    async def send(self, notification: Notification):
        """Отправка уведомления"""
        handler = self._handlers.get(notification.channel)
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(notification)
                else:
                    handler(notification)
            except Exception as e:
                logger.error(f"Notification error: {e}")
        else:
            logger.warning(f"No handler for channel: {notification.channel}")


class NotificationManager:
    """
    Менеджер уведомлений
    """

    def __init__(self):
        self._handlers: dict[NotificationChannel, NotificationHandler] = {}
        self._subscribers: list[Callable] = []

    def register_channel(
        self,
        channel: NotificationChannel,
        handler: Callable,
    ):
        """Регистрация канала"""
        if channel not in self._handlers:
            self._handlers[channel] = NotificationHandler(channel)
        self._handlers[channel].register_handler(channel, handler)
        logger.info(f"Registered notification channel: {channel.value}")

    def subscribe(self, callback: Callable):
        """Подписка на уведомления"""
        self._subscribers.append(callback)

    async def notify(
        self,
        level: NotificationLevel,
        title: str,
        message: str,
        channel: NotificationChannel = NotificationChannel.CONSOLE,
        metadata: dict = None,
    ):
        """Отправка уведомления"""
        notification = Notification(
            level=level,
            title=title,
            message=message,
            channel=channel,
            metadata=metadata or {},
        )

        # Send to channel handler
        handler = self._handlers.get(channel)
        if handler:
            await handler.send(notification)

        # Notify subscribers
        for sub in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(sub):
                    await sub(notification)
                else:
                    sub(notification)
            except Exception as e:
                logger.error(f"Subscriber error: {e}")

    async def debug(self, title: str, message: str, **kwargs):
        """Отладка"""
        await self.notify(NotificationLevel.DEBUG, title, message, **kwargs)

    async def info(self, title: str, message: str, **kwargs):
        """Инфо"""
        await self.notify(NotificationLevel.INFO, title, message, **kwargs)

    async def warning(self, title: str, message: str, **kwargs):
        """Предупреждение"""
        await self.notify(NotificationLevel.WARNING, title, message, **kwargs)

    async def error(self, title: str, message: str, **kwargs):
        """Ошибка"""
        await self.notify(NotificationLevel.ERROR, title, message, **kwargs)

    async def critical(self, title: str, message: str, **kwargs):
        """Критическая ошибка"""
        await self.notify(NotificationLevel.CRITICAL, title, message, **kwargs)


# Built-in handlers

async def console_handler(notification: Notification):
    """Обработчик для консоли"""
    level_str = notification.level.value.upper()
    print(f"[{level_str}] {notification.title}: {notification.message}")


async def email_handler(notification: Notification):
    """Обработчик для email (mock)"""
    logger.info(f"EMAIL to admin: {notification.title}")


async def slack_handler(notification: Notification):
    """Обработчик для Slack (mock)"""
    logger.info(f"SLACK: {notification.title}")


# Singleton
_notification_manager: NotificationManager | None = None


def get_notification_manager() -> NotificationManager:
    """Получение менеджера уведомлений"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
