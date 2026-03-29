"""WebSocket client"""

import logging
from collections.abc import Callable

logger = logging.getLogger("orchestration.ws_client")


class WSClient:
    """WebSocket client"""

    def __init__(self, url: str):
        self.url = url
        self.connected = False
        self.handlers: dict[str, Callable] = {}

    def connect(self):
        logger.info(f"Connecting to {self.url}")
        self.connected = True

    def disconnect(self):
        logger.info("Disconnected")
        self.connected = False

    def send(self, message: dict):
        if self.connected:
            logger.info(f"Sending: {message}")

    def on(self, event: str, handler: Callable):
        self.handlers[event] = handler

    def receive(self, message: dict):
        event = message.get("type")
        if event in self.handlers:
            self.handlers[event](message)
