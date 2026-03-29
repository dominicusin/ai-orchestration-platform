"""Pipeline notifications channels"""

import logging

logger = logging.getLogger("orchestration.notification_channels")


class NotificationChannel:
    """Base notification channel"""

    def send(self, message: str, data: dict = None):
        raise NotImplementedError


class LogChannel(NotificationChannel):
    """Log notification channel"""

    def send(self, message: str, data: dict = None):
        logger.info(f"Notification: {message}")


class FileChannel(NotificationChannel):
    """File notification channel"""

    def __init__(self, path: str):
        self.path = path

    def send(self, message: str, data: dict = None):
        from pathlib import Path
        Path(self.path).write_text(Path(self.path).read_text() + f"{message}\n")


class ChannelManager:
    """Manage notification channels"""

    def __init__(self):
        self.channels = []

    def add(self, channel: NotificationChannel):
        self.channels.append(channel)

    def notify(self, message: str, data: dict = None):
        for channel in self.channels:
            channel.send(message, data)

