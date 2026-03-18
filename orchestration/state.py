"""State management for DAG execution"""

import json
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("orchestration.state")


@dataclass
class ExecutionState:
    """Current execution state"""
    execution_id: str
    status: str  # running, paused, completed, failed
    current_layer: int = 0
    total_layers: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    started_at: str = ""
    updated_at: str = ""
    metadata: Dict = None
    
    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class StateManager:
    """Manage execution state"""
    
    def __init__(self, state_dir: str = "./state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.current_state: Optional[ExecutionState] = None
    
    def create(self, execution_id: str, total_layers: int) -> ExecutionState:
        """Create new execution state"""
        self.current_state = ExecutionState(
            execution_id=execution_id,
            status="running",
            total_layers=total_layers,
        )
        self._save()
        return self.current_state
    
    def update(self, **kwargs):
        """Update state"""
        if self.current_state:
            for key, value in kwargs.items():
                if hasattr(self.current_state, key):
                    setattr(self.current_state, key, value)
            self.current_state.updated_at = datetime.now().isoformat()
            self._save()
    
    def get(self) -> Optional[ExecutionState]:
        """Get current state"""
        return self.current_state
    
    def load(self, execution_id: str) -> Optional[ExecutionState]:
        """Load state from disk"""
        path = self.state_dir / f"{execution_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            self.current_state = ExecutionState(**data)
            return self.current_state
        return None
    
    def _save(self):
        """Save state to disk"""
        if self.current_state:
            path = self.state_dir / f"{self.current_state.execution_id}.json"
            path.write_text(self.current_state.to_json())
    
    def delete(self, execution_id: str):
        """Delete state"""
        path = self.state_dir / f"{execution_id}.json"
        if path.exists():
            path.unlink()


class StateCheckpoint:
    """Checkpoint state for recovery"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
    
    def checkpoint(self, task_id: str, result: Any):
        """Create checkpoint"""
        state = self.state_manager.get()
        if state:
            state.metadata = state.metadata or {}
            state.metadata[f"task_{task_id}"] = {
                "result": str(result)[:1000],  # Truncate
                "timestamp": datetime.now().isoformat(),
            }
            self.state_manager.update()
    
    def recover(self) -> Dict:
        """Recover from checkpoint"""
        state = self.state_manager.get()
        if state and state.metadata:
            return state.metadata
        return {}


# Global state manager
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get state manager"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager