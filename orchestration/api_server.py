```python
"""REST API Server for pipeline"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Try FastAPI, fallback to basic
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None

logger = logging.getLogger("orchestration.api")


# Pydantic models
class ConvertRequest(BaseModel):
    code: str
    source_format: str
    target_format: str
    options: Optional[Dict[str, Any]] = {}


class ConvertResponse(BaseModel):
    success: bool
    output: str
    errors: List[str] = []


class StatusResponse(BaseModel):
    running: bool
    phase: str
    progress: int
    files_processed: int


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


def create_app() -> FastAPI:
    """Create FastAPI application"""
    if not FASTAPI_AVAILABLE:
        return None
    
    app = FastAPI(
        title="AI Pipeline API",
        description="C++ to Haskell/QML/Reports converter",
        version="1.0.0",
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # State
    app.state.pipeline = None
    app.state.running = False
    app.state.current_phase = ""
    app.state.progress = 0
    
    @app.get("/health", response_model=HealthResponse)
    async def health():
        return HealthResponse(
            status="ok",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
        )
    
    @app.get("/api/status", response_model=StatusResponse)
    async def get_status():
        return StatusResponse(
            running=app.state.running,
            phase=app.state.current_phase,
            progress=app.state.progress,
            files_processed=_count_files(),
        )
    
    @app.post("/api/convert", response_model=ConvertResponse)
    async def convert(request: ConvertRequest):
        """Convert code between formats"""
        try:
            # Would call AI here
            output = f"# Converted from {request.source_format} to {request.target_format}\n{request.code[:100]}"
            
            return ConvertResponse(
                success=True,
                output=output,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/pipeline/start")
    async def start_pipeline(background_tasks: BackgroundTasks):
        """Start pipeline"""
        if app.state.running:
            raise HTTPException(status_code=400, detail="Pipeline already running")
        
        app.state.running = True
        # Would start pipeline in background
        # background_tasks.add_task(run_pipeline_task, app)
        
        return {"status": "started"}
    
    @app.post("/api/pipeline/stop")
    async def stop_pipeline():
        """Stop pipeline"""
        app.state.running = False
        return {"status": "stopped"}
    
    @app.get("/api/files")
    async def list_files(file_type: str = None):
        """List generated files"""
        base = Path("./Surypus2")
        files = []
        
        if file_type == "haskell":
            files = list(base.glob("src/*.hs"))
        elif file_type == "qml":
            files = list(base.glob("qml/*.qml"))
        elif file_type == "reports":
            files = list(base.glob("reports/**/*"))
        else:
            files = list(base.glob("**/*"))
        
        return {
            "files": [
                {
                    "path": str(f.relative_to(base)),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                }
                for f in files if f.is_file()
            ]
        }
    
    @app.get("/api/metrics")
    async def get_metrics():
        """Get pipeline metrics"""
        metrics_file = Path("./Surypus2/metrics.json")
        if metrics_file.exists():
            return json.loads(metrics_file.read_text())
        return {"error": "No metrics available"}
    
    @app.post("/api/cache/clear")
    async def clear_cache():
        """Clear cache"""
        cache_dir = Path("./Surypus2/.cache")
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
        return {"status": "cache cleared"}
    
    return app


def _count_files() -> int:
    """Count generated files"""
    base = Path("./Surypus2")
    if not base.exists():
        return 0
    
    count = 0
    for ext in ["*.hs", "*.qml", "*.jrxml", "*.xaction", "*.yaml"]:
        count += len(list(base.glob(f"**/{ext}")))
    return count


# Standalone server
def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start API server"""
    if not FASTAPI_AVAILABLE:
        print("FastAPI not available, install with: pip install fastapi uvicorn")
        return
    
    import uvicorn
    app = create_app()
    
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    
    print(f"🌐 API Server: http://{host}:{port}")
    print(f"   Docs: http://{host}:{port}/docs")
    
    server.run()


if __name__ == "__main__":
    start_server()
```