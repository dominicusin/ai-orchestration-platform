"""WebSocket client for real-time communication"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("orchestration.ws_client")


class WSClientState(Enum):
    """WebSocket client state"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


@dataclass
class WSMessage:
    """WebSocket message"""
    type: str
    data: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class WSClient:
    """WebSocket client for real-time updates"""
    
    def __init__(
        self,
        url: str = "ws://localhost:8765",
        reconnect: bool = True,
        reconnect_delay: float = 5.0,
    ):
        self.url = url
        self.reconnect = reconnect
        self.reconnect_delay = reconnect_delay
        
        self.state = WSClientState.DISCONNECTED
        self.ws = None
        self.handlers: Dict[str, Callable] = {}
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """Connect to WebSocket server"""
        if self.state in [WSClientState.CONNECTING, WSClientState.CONNECTED]:
            return True
        
        self.state = WSClientState.CONNECTING
        
        try:
            import websockets
            
            self.ws = await websockets.connect(self.url)
            self.state = WSClientState.CONNECTED
            
            logger.info(f"Connected to {self.url}")
            
            # Start receiving
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.state = WSClientState.DISCONNECTED
            
            if self.reconnect:
                await self._schedule_reconnect()
            
            return False
    
    async def disconnect(self):
        """Disconnect from server"""
        self.reconnect = False
        
        if self._receive_task:
            self._receive_task.cancel()
        
        if self.ws:
            await self.ws.close()
        
        self.state = WSClientState.DISCONNECTED
        logger.info("Disconnected")
    
    async def send(self, message: WSMessage):
        """Send message to server"""
        if self.state != WSClientState.CONNECTED or not self.ws:
            logger.warning("Not connected, cannot send message")
            return
        
        try:
            await self.ws.send(json.dumps({
                "type": message.type,
                "data": message.data,
                "timestamp": message.timestamp,
            }))
        except Exception as e:
            logger.error(f"Send failed: {e}")
    
    async def send_raw(self, data: Dict):
        """Send raw data"""
        await self.send(WSMessage(type=data.get("type", "message"), data=data))
    
    async def _receive_loop(self):
        """Receive messages loop"""
        try:
            async for message in self.ws:
                await self._handle_message(message)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Receive error: {e}")
            
            if self.reconnect:
                await self._schedule_reconnect()
    
    async def _handle_message(self, raw: str):
        """Handle incoming message"""
        try:
            data = json.loads(raw)
            msg_type = data.get("type", "message")
            
            # Call handler
            if msg_type in self.handlers:
                await self.handlers[msg_type](data.get("data", {}))
            
            # Call wildcard handler
            if "*" in self.handlers:
                await self.handlers["*"](data)
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON: {raw}")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    async def _schedule_reconnect(self):
        """Schedule reconnection"""
        if self._reconnect_task:
            return
        
        self.state = WSClientState.RECONNECTING
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())
    
    async def _reconnect_loop(self):
        """Reconnection loop"""
        while self.reconnect and self.state == WSClientState.RECONNECTING:
            logger.info(f"Reconnecting in {self.reconnect_delay}s...")
            await asyncio.sleep(self.reconnect_delay)
            
            if await self.connect():
                self._reconnect_task = None
                return
    
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.handlers[event_type] = handler
    
    def off(self, event_type: str):
        """Remove event handler"""
        if event_type in self.handlers:
            del self.handlers[event_type]
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status"""
        return {
            "state": self.state.value,
            "url": self.url,
            "reconnect": self.reconnect,
            "handlers": list(self.handlers.keys()),
        }


class PipelineWSClient(WSClient):
    """WebSocket client for pipeline events"""
    
    def __init__(self, url: str = "ws://localhost:8765"):
        super().__init__(url)
        
        # Register default handlers
        self.on("pipeline.start", self._on_pipeline_start)
        self.on("pipeline.complete", self._on_pipeline_complete)
        self.on("phase.start", self._on_phase_start)
        self.on("phase.complete", self._on_phase_complete)
        self.on("file.converted", self._on_file_converted)
        self.on("error", self._on_error)
    
    async def _on_pipeline_start(self, data: Dict):
        logger.info(f"Pipeline started: {data}")
    
    async def _on_pipeline_complete(self, data: Dict):
        logger.info(f"Pipeline completed: {data}")
    
    async def _on_phase_start(self, data: Dict):
        logger.info(f"Phase started: {data}")
    
    async def _on_phase_complete(self, data: Dict):
        logger.info(f"Phase completed: {data}")
    
    async def _on_file_converted(self, data: Dict):
        logger.debug(f"File converted: {data}")
    
    async def _on_error(self, data: Dict):
        logger.error(f"Pipeline error: {data}")


# Global client
_ws_client: Optional[WSClient] = None


def get_ws_client(url: str = None) -> WSClient:
    """Get WebSocket client"""
    global _ws_client
    if _ws_client is None:
        _ws_client = WSClient(url or "ws://localhost:8765")
    return _ws_client
