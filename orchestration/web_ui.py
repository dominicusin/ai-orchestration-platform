"""Web UI для мониторинга pipeline"""

import json
import os
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import urllib.parse


class PipelineHandler(BaseHTTPRequestHandler):
    """HTTP обработчик для pipeline мониторинга"""
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == "/" or path == "/index.html":
            self.send_html(self.dashboard())
        elif path == "/api/status":
            self.send_json(self.get_status())
        elif path == "/api/metrics":
            self.send_json(self.get_metrics())
        elif path == "/api/logs":
            self.send_json(self.get_logs())
        elif path == "/health":
            self.send_json({"status": "ok", "timestamp": datetime.now().isoformat()})
        else:
            self.send_error(404)
    
    def get_status(self):
        """Получение статуса pipeline"""
        output_path = Path("./Surypus2")
        
        status = {
            "running": False,
            "phases": {},
            "files": {},
            "errors": 0,
        }
        
        # Проверяем файлы
        src_count = len(list(output_path.glob("src/*.hs"))) if output_path.exists() else 0
        qml_count = len(list(output_path.glob("qml/*.qml"))) if output_path.exists() else 0
        jasper_count = len(list(output_path.glob("reports/jasper/*.jrxml"))) if output_path.exists() else 0
        
        status["files"] = {
            "haskell": src_count,
            "qml": qml_count,
            "jasper": jasper_count,
            "total": src_count + qml_count + jasper_count,
        }
        
        # Читаем state
        state_file = output_path / ".pipeline_state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                status["phases"] = state
            except:
                pass
        
        return status
    
    def get_metrics(self):
        """Получение метрик"""
        output_path = Path("./Surypus2/metrics.json")
        if output_path.exists():
            try:
                return json.loads(output_path.read_text())
            except:
                pass
        return {"error": "No metrics"}
    
    def get_logs(self):
        """Получение логов"""
        log_file = Path("./Surypus2/pipeline.log")
        if log_file.exists():
            lines = log_file.read_text().splitlines()[-50:]
            return {"logs": lines, "count": len(lines)}
        return {"logs": [], "count": 0}
    
    def dashboard(self):
        """HTML dashboard"""
        return """<!DOCTYPE html>
<html>
<head>
    <title>AI Pipeline Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: #1a1a2e; color: #eee; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { color: #00d4ff; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .card { background: #16213e; border-radius: 12px; padding: 20px; border: 1px solid #0f3460; }
        .card h2 { color: #00d4ff; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; }
        .stat { font-size: 36px; font-weight: bold; color: #fff; }
        .stat.haskell { color: #5c8aff; }
        .stat.qml { color: #ff6b6b; }
        .stat.reports { color: #4ecdc4; }
        .stat.error { color: #ff4757; }
        .phase { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #0f3460; }
        .phase:last-child { border: none; }
        .phase-name { color: #aaa; }
        .phase-status { font-weight: bold; }
        .phase-status.done { color: #4ecdc4; }
        .phase-status.pending { color: #666; }
        .logs { background: #0f0f1a; padding: 15px; border-radius: 8px; max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px; }
        .log-line { padding: 2px 0; color: #888; }
        .log-line.error { color: #ff4757; }
        .log-line.warning { color: #ffa502; }
        .log-line.info { color: #00d4ff; }
        .btn { display: inline-block; padding: 10px 20px; background: #00d4ff; color: #1a1a2e; 
               border-radius: 6px; text-decoration: none; font-weight: bold; margin-right: 10px; }
        .btn:hover { background: #00b8e6; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .timestamp { color: #666; font-size: 12px; }
    </style>
    <script>
        async function update() {
            try {
                const status = await fetch('/api/status').then(r => r.json());
                const metrics = await fetch('/api/metrics').then(r => r.json());
                
                document.getElementById('haskell').textContent = status.files.haskell || 0;
                document.getElementById('qml').textContent = status.files.qml || 0;
                document.getElementById('reports').textContent = status.files.jasper || 0;
                document.getElementById('total').textContent = status.files.total || 0;
                
                if (metrics.runtime_seconds) {
                    const mins = Math.floor(metrics.runtime_seconds / 60);
                    const secs = Math.floor(metrics.runtime_seconds % 60);
                    document.getElementById('runtime').textContent = mins + 'm ' + secs + 's';
                }
            } catch(e) { console.error(e); }
        }
        setInterval(update, 5000);
        update();
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Pipeline Monitor</h1>
            <span class="timestamp">""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</span>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Haskell Files</h2>
                <div class="stat haskell" id="haskell">0</div>
            </div>
            <div class="card">
                <h2>QML Files</h2>
                <div class="stat qml" id="qml">0</div>
            </div>
            <div class="card">
                <h2>Reports</h2>
                <div class="stat reports" id="reports">0</div>
            </div>
            <div class="card">
                <h2>Runtime</h2>
                <div class="stat" id="runtime">0m 0s</div>
            </div>
        </div>
        
        <div class="grid" style="margin-top: 20px;">
            <div class="card">
                <h2>Total Files</h2>
                <div class="stat" id="total">0</div>
            </div>
            <div class="card">
                <h2>Actions</h2>
                <a href="/api/status" class="btn">Refresh</a>
                <a href="/health" class="btn" style="background: #4ecdc4;">Health</a>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def start_server(port: int = 8080):
    """Запуск web сервера"""
    server = HTTPServer(("0.0.0.0", port), PipelineHandler)
    print(f"🌐 Web UI: http://localhost:{port}")
    print(f"📊 API: http://localhost:{port}/api/status")
    print(f"💚 Health: http://localhost:{port}/health")
    server.serve_forever()


if __name__ == "__main__":
    start_server()
