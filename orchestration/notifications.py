"""Notifications system"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("orchestration.notifications")


class Notification:
    """Notification message"""
    
    def __init__(self, title: str, message: str, level: str = "info"):
        self.title = title
        self.message = message
        self.level = level


class NotificationChannel:
    """Base notification channel"""
    
    def send(self, notification: Notification):
        raise NotImplementedError


class LogChannel(NotificationChannel):
    """Log notifications"""
    
    def send(self, notification: Notification):
        logger.info(f"[{notification.level}] {notification.title}: {notification.message}")


class NotificationManager:
    """Manage notifications"""
    
    def __init__(self):
        self.channels: List[NotificationChannel] = [LogChannel()]
    
    def add_channel(self, channel: NotificationChannel):
        self.channels.append(channel)
    
    def notify(self, title: str, message: str, level: str = "info"):
        notification = Notification(title, message, level)
        for channel in self.channels:
            channel.send(notification)
