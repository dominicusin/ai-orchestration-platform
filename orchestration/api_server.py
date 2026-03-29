"""API server for DAG execution"""

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger("orchestration.api_server")


class APIHandler(BaseHTTPRequestHandler):
    """API request handler"""

    def do_GET(self):
        if self.path == "/health":
            self.send_json({"status": "ok"})
        elif self.path == "/api/tasks":
            self.send_json({"tasks": []})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/tasks":
            self.send_json({"status": "created"})
        else:
            self.send_error(404)

    def send_json(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


class APIServer:
    """REST API server"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.server = None

    def start(self):
        self.server = HTTPServer((self.host, self.port), APIHandler)
        logger.info(f"API server at http://{self.host}:{self.port}")
        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.shutdown()


_server = None


def get_api_server() -> APIServer:
    global _server
    if _server is None:
        _server = APIServer()
    return _server
