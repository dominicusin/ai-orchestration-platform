"""Web UI for DAG monitoring"""

import json
import logging
from typing import Dict, Any, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger("orchestration.web_ui")


class PipelineHandler:
    """Legacy pipeline handler for compatibility"""
    
    # Class attributes for __new__ compatibility
    dashboard_data = "AI Pipeline Monitor - Haskell QML"
    
    def __init__(self):
        pass
    
    def dashboard(self):
        return self.dashboard_data
    
    def handle(self, path: str) -> str:
        return "OK"


class DAGRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for DAG monitoring UI"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/" or path == "/index.html":
            self.send_html(self.get_main_page())
        elif path == "/api/status":
            self.send_json(self.get_status())
        elif path == "/api/metrics":
            self.send_json(self.get_metrics())
        elif path == "/api/tasks":
            self.send_json(self.get_tasks())
        elif path == "/api/layers":
            self.send_json(self.get_layers())
        elif path == "/api/dag":
            self.send_json(self.get_dag())
        else:
            self.send_error(404)
    
    def send_html(self, html: str):
        """Send HTML response"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json(self, data: Dict):
        """Send JSON response"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_main_page(self) -> str:
        """Get main HTML page"""
        return """<!DOCTYPE html>
<html>
<head>
    <title>DAG Execution Monitor</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: #1a1a2e; color: #eee; padding: 20px; }
        h1 { color: #00d4ff; margin-bottom: 20px; }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .card { background: #16213e; padding: 20px; border-radius: 8px; border: 1px solid #0f3460; }
        .card h3 { color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 8px; }
        .card .value { font-size: 28px; font-weight: bold; color: #00d4ff; }
        .card.success .value { color: #00ff88; }
        .card.failed .value { color: #ff4757; }
        .section { background: #16213e; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section h2 { color: #00d4ff; margin-bottom: 15px; font-size: 18px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #0f3460; }
        th { color: #888; font-weight: 500; }
        .status-running { color: #ffd700; }
        .status-completed { color: #00ff88; }
        .status-failed { color: #ff4757; }
        .layer { display: flex; align-items: center; gap: 10px; padding: 10px; background: #0f3460; margin-bottom: 5px; border-radius: 4px; }
        .layer-num { background: #00d4ff; color: #000; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
        .layer-tasks { flex: 1; color: #aaa; }
        .refresh { position: fixed; top: 20px; right: 20px; background: #00d4ff; color: #000; 
                   border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>🔄 DAG Execution Monitor</h1>
    <button class="refresh" onclick="location.reload()">Refresh</button>
    
    <div class="dashboard" id="dashboard"></div>
    
    <div class="section">
        <h2>📊 Execution Layers</h2>
        <div id="layers"></div>
    </div>
    
    <div class="section">
        <h2>📋 Recent Tasks</h2>
        <table>
            <thead><tr><th>Task</th><th>Layer</th><th>Status</th><th>Duration</th></tr></thead>
            <tbody id="tasks"></tbody>
        </table>
    </div>
    
    <script>
        async function update() {
            const status = await fetch('/api/status').then(r => r.json());
            const metrics = await fetch('/api/metrics').then(r => r.json());
            const tasks = await fetch('/api/tasks').then(r => r.json());
            const layers = await fetch('/api/layers').then(r => r.json());
            
            document.getElementById('dashboard').innerHTML = `
                <div class="card"><h3>Total Tasks</h3><div class="value">${status.total_tasks}</div></div>
                <div class="card success"><h3>Completed</h3><div class="value">${status.completed}</div></div>
                <div class="card failed"><h3>Failed</h3><div class="value">${status.failed}</div></div>
                <div class="card"><h3>Success Rate</h3><div class="value">${(status.success_rate * 100).toFixed(1)}%</div></div>
                <div class="card"><h3>Duration</h3><div class="value">${status.total_duration.toFixed(1)}s</div></div>
            `;
            
            document.getElementById('layers').innerHTML = layers.map(l => `
                <div class="layer">
                    <span class="layer-num">L${l.layer}</span>
                    <span class="layer-tasks">${l.tasks} tasks</span>
                    <span>${l.completed} ✓</span>
                    <span>${l.failed} ✗</span>
                    <span>${l.duration.toFixed(2)}s</span>
                </div>
            `).join('');
            
            document.getElementById('tasks').innerHTML = tasks.slice(0, 20).map(t => `
                <tr>
                    <td>${t.task_name}</td>
                    <td>${t.layer}</td>
                    <td class="status-${t.status}">${t.status}</td>
                    <td>${t.duration.toFixed(3)}s</td>
                </tr>
            `).join('');
        }
        
        update();
        setInterval(update, 2000);
    </script>
</body>
</html>"""
    
    def get_status(self) -> Dict:
        """Get execution status"""
        from orchestration.graph_monitor import get_monitor
        return get_monitor().get_summary()
    
    def get_metrics(self) -> Dict:
        """Get metrics"""
        from orchestration.graph_monitor import get_monitor
        return get_monitor().get_summary()
    
    def get_tasks(self) -> List[Dict]:
        """Get tasks"""
        from orchestration.graph_monitor import get_monitor
        m = get_monitor()
        return [
            {
                "task_id": t.task_id,
                "task_name": t.task_name,
                "layer": t.layer,
                "status": t.status,
                "duration": t.duration,
            }
            for t in m.task_metrics.values()
        ]
    
    def get_layers(self) -> List[Dict]:
        """Get layer info"""
        from orchestration.graph_monitor import get_monitor
        return get_monitor().get_layer_summary()
    
    def get_dag(self) -> Dict:
        """Get DAG structure"""
        return {"nodes": [], "edges": []}


class WebUIServer:
    """Web UI server"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.server = None
    
    def start(self):
        """Start server"""
        self.server = HTTPServer((self.host, self.port), DAGRequestHandler)
        logger.info(f"DAG Monitor UI: http://{self.host}:{self.port}")
        self.server.serve_forever()
    
    def stop(self):
        """Stop server"""
        if self.server:
            self.server.shutdown()


# Global server
_server: Optional[WebUIServer] = None


def start_ui(host: str = "localhost", port: int = 8080):
    """Start web UI"""
    global _server
    _server = WebUIServer(host, port)
    _server.start()


if __name__ == "__main__":
    start_ui()