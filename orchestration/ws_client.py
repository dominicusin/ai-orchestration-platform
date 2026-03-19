"""WebSocket client"""

import logging
from typing import Callable, Dict, Any

logger = logging.getLogger("orchestration.ws_client")


class WSClient:
    """WebSocket client"""
    
    def __init__(self, url: str):
        self.url = url
        self.connected = False
        self.handlers: Dict[str, Callable] = {}
    
    def connect(self):
        logger.info(f"Connecting to {self.url}")
        self.connected = True
    
    def disconnect(self):
        logger.info("Disconnected")
        self.connected = False
    
    def send(self, message: Dict):
        if self.connected:
            logger.info(f"Sending: {message}")
    
    def on(self, event: str, handler: Callable):
        self.handlers[event] = handler
    
    def receive(self, message: Dict):
        event = message.get("type")
        if event in self.handlers:
            self.handlers[event](message)