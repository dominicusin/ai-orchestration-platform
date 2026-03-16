"""Pipeline checkpoints"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("orchestration.checkpoints")


class CheckpointManager:
    """Manage pipeline checkpoints"""
    
    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, name: str, data: Dict):
        """Save checkpoint"""
        path = self.checkpoint_dir / f"{name}.json"
        path.write_text(json.dumps(data, indent=2))
    
    def load(self, name: str) -> Optional[Dict]:
        """Load checkpoint"""
        path = self.checkpoint_dir / f"{name}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None
    
    def delete(self, name: str):
        """Delete checkpoint"""
        path = self.checkpoint_dir / f"{name}.json"
        if path.exists():
            path.unlink()
    
    def list(self) -> list:
        """List checkpoints"""
        return [p.stem for p in self.checkpoint_dir.glob("*.json")]
