"""WebSocket server for real-time updates"""

import logging
from typing import Dict, Any, List, Callable

logger = logging.getLogger("orchestration.websocket_server")


class WebSocketConnection:
    """WebSocket connection"""
    
    def __init__(self, conn_id: str):
        self.conn_id = conn_id
        self.handlers: List[Callable] = []
    
    def send(self, message: Dict):
        logger.info(f"WS {self.conn_id}: {message}")
    
    def close(self):
        logger.info(f"WS {self.conn_id} closed")


class WebSocketServer:
    """WebSocket server"""
    
    def __init__(self, port: int = 8081):
        self.port = port
        self.connections: Dict[str, WebSocketConnection] = {}
    
    def add_connection(self, conn_id: str) -> WebSocketConnection:
        conn = WebSocketConnection(conn_id)
        self.connections[conn_id] = conn
        return conn
    
    def remove_connection(self, conn_id: str):
        if conn_id in self.connections:
            del self.connections[conn_id]
    
    def broadcast(self, message: Dict):
        for conn in self.connections.values():
            conn.send(message)
    
    def start(self):
        logger.info(f"WebSocket server would start on port {self.port}")


_server = None


def get_ws_server() -> WebSocketServer:
    global _server
    if _server is None:
        _server = WebSocketServer()
    return _server