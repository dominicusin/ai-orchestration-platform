"""WebSocket support for real-time updates"""

import asyncio
import json
import logging
from typing import Dict, Set, Any, Callable, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger("orchestration.websocket")


@dataclass
class WSMessage:
    """WebSocket message"""
    type: str
    data: Dict[str, Any]
    timestamp: str


class WebSocketManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.connections: Set[Any] = set()
        self.handlers: Dict[str, Callable] = {}
    
    def add_connection(self, websocket):
        """Add WebSocket connection"""
        self.connections.add(websocket)
        logger.info(f"WebSocket connected: {len(self.connections)} total")
    
    def remove_connection(self, websocket):
        """Remove WebSocket connection"""
        self.connections.discard(websocket)
        logger.info(f"WebSocket disconnected: {len(self.connections)} remaining")
    
    async def broadcast(self, message: WSMessage):
        """Broadcast message to all connections"""
        if not self.connections:
            return
        
        message_str = json.dumps({
            "type": message.type,
            "data": message.data,
            "timestamp": message.timestamp,
        })
        
        # Send to all (in parallel)
        tasks = []
        for ws in list(self.connections):
            try:
                tasks.append(ws.send_text(message_str))
            except Exception:
                self.connections.discard(ws)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_to(self, websocket, message: WSMessage):
        """Send message to specific client"""
        try:
            await websocket.send_json({
                "type": message.type,
                "data": message.data,
                "timestamp": message.timestamp,
            })
        except Exception as e:
            logger.error(f"Failed to send: {e}")
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register message handler"""
        self.handlers[event_type] = handler
    
    async def handle_message(self, websocket, message: Dict[str, Any]):
        """Handle incoming message"""
        msg_type = message.get("type")
        data = message.get("data", {})
        
        if msg_type in self.handlers:
            await self.handlers[msg_type](websocket, data)


class RealtimePipeline:
    """Pipeline with real-time updates"""
    
    def __init__(self):
        self.ws_manager = WebSocketManager()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup message handlers"""
        self.ws_manager.register_handler("ping", self._handle_ping)
        self.ws_manager.register_handler("subscribe", self._handle_subscribe)
    
    async def _handle_ping(self, websocket, data: Dict):
        """Handle ping"""
        await self.ws_manager.send_to(websocket, WSMessage(
            type="pong",
            data={"time": datetime.now().isoformat()},
            timestamp=datetime.now().isoformat(),
        ))
    
    async def _handle_subscribe(self, websocket, data: Dict):
        """Handle subscription"""
        # Would subscribe to specific events
        await self.ws_manager.send_to(websocket, WSMessage(
            type="subscribed",
            data=data,
            timestamp=datetime.now().isoformat(),
        ))
    
    async def broadcast_phase_start(self, phase: str, total: int):
        """Broadcast phase start"""
        await self.ws_manager.broadcast(WSMessage(
            type="phase.start",
            data={"phase": phase, "total": total},
            timestamp=datetime.now().isoformat(),
        ))
    
    async def broadcast_phase_progress(self, phase: str, current: int, total: int):
        """Broadcast phase progress"""
        await self.ws_manager.broadcast(WSMessage(
            type="phase.progress",
            data={"phase": phase, "current": current, "total": total},
            timestamp=datetime.now().isoformat(),
        ))
    
    async def broadcast_phase_complete(self, phase: str, files: int, duration: float):
        """Broadcast phase complete"""
        await self.ws_manager.broadcast(WSMessage(
            type="phase.complete",
            data={"phase": phase, "files": files, "duration": duration},
            timestamp=datetime.now().isoformat(),
        ))
    
    async def broadcast_file_converted(self, file_path: str, format: str):
        """Broadcast file converted"""
        await self.ws_manager.broadcast(WSMessage(
            type="file.converted",
            data={"path": file_path, "format": format},
            timestamp=datetime.now().isoformat(),
        ))
    
    async def broadcast_error(self, error: str, context: str):
        """Broadcast error"""
        await self.ws_manager.broadcast(WSMessage(
            type="error",
            data={"error": error, "context": context},
            timestamp=datetime.now().isoformat(),
        ))


# Standalone WebSocket server
async def websocket_echo(websocket, path):
    """Echo WebSocket handler"""
    manager = WebSocketManager()
    manager.add_connection(websocket)
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"time": datetime.now().isoformat()},
                    })
                else:
                    # Echo back
                    await websocket.send_json(data)
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON"},
                })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.remove_connection(websocket)


def start_websocket_server(port: int = 8765):
    """Start WebSocket server"""
    import websockets
    
    logger.info(f"Starting WebSocket server on port {port}")
    
    async def handler(websocket, path):
        await websocket_echo(websocket, path)
    
    start_server = websockets.serve(handler, "0.0.0.0", port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


# Try to import websockets
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


# Client example
class WSClient:
    """WebSocket client for testing"""
    
    def __init__(self, url: str = "ws://localhost:8765"):
        self.url = url
        self.ws = None
    
    async def connect(self):
        """Connect to server"""
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets not installed")
        
        self.ws = await websockets.connect(self.url)
        logger.info(f"Connected to {self.url}")
    
    async def send(self, message: Dict):
        """Send message"""
        if self.ws:
            await self.ws.send(json.dumps(message))
    
    async def receive(self) -> Dict:
        """Receive message"""
        if self.ws:
            return json.loads(await self.ws.recv())
    
    async def close(self):
        """Close connection"""
        if self.ws:
            await self.ws.close()
