"""Dashboard for execution monitoring"""

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger("orchestration.dashboard")


class DashboardHandler(BaseHTTPRequestHandler):
    """Dashboard HTTP handler"""

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(self.get_dashboard().encode())
        elif self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.get_stats()).encode())
        else:
            self.send_error(404)

    def get_dashboard(self) -> str:
        return """<!DOCTYPE html>
<html><head><title>DAG Dashboard</title></head>
<body><h1>DAG Execution Dashboard</h1>
<div id="stats"></div>
<script>
fetch('/api/stats').then(r=>r.json()).then(d=>{
    document.getElementById('stats').innerHTML =
        'Tasks: ' + d.tasks + '<br>Completed: ' + d.completed;
});
</script></body></html>"""

    def get_stats(self) -> dict:
        from orchestration.graph_monitor import get_monitor
        return get_monitor().get_summary()


def start_dashboard(port: int = 8080):
    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    logger.info(f"Dashboard at http://localhost:{port}")
    server.serve_forever()
