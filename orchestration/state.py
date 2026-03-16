"""Pipeline state management with persistence"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger("orchestration.state")


class PipelinePhase(Enum):
    """Pipeline phases"""
    INIT = "init"
    ANALYSIS = "analysis"
    DATABASE = "database"
    HASKELL = "haskell"
    QML = "qml"
    REPORTS = "reports"
    COMPLETE = "complete"
    FAILED = "failed"


class PhaseStatus(Enum):
    """Phase status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseState:
    """State of a single phase"""
    name: str
    status: str = PhaseStatus.PENDING.value
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    files_processed: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineState:
    """Complete pipeline state"""
    project_path: str
    output_path: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = "pending"
    current_phase: str = ""
    phases: Dict[str, PhaseState] = field(default_factory=dict)
    total_files: int = 0
    converted_files: int = 0
    failed_files: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Initialize phases
        for phase in PipelinePhase:
            if phase.value not in self.phases:
                self.phases[phase.value] = PhaseState(name=phase.value)


class StateManager:
    """Manage pipeline state persistence"""
    
    def __init__(self, state_file: str = ".pipeline_state.json"):
        self.state_file = Path(state_file)
        self.state: Optional[PipelineState] = None
    
    def create(self, project_path: str, output_path: str) -> PipelineState:
        """Create new state"""
        state = PipelineState(
            project_path=project_path,
            output_path=output_path,
            started_at=datetime.now().isoformat(),
            status="running",
        )
        
        self.state = state
        self.save()
        
        logger.info(f"Created pipeline state: {project_path} -> {output_path}")
        
        return state
    
    def load(self) -> Optional[PipelineState]:
        """Load state from file"""
        if not self.state_file.exists():
            return None
        
        try:
            data = json.loads(self.state_file.read_text())
            
            # Reconstruct phases
            phases = {}
            for name, phase_data in data.get("phases", {}).items():
                phases[name] = PhaseState(**phase_data)
            
            data["phases"] = phases
            
            self.state = PipelineState(**data)
            
            return self.state
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    def save(self):
        """Save state to file"""
        if not self.state:
            return
        
        data = {
            "project_path": self.state.project_path,
            "output_path": self.state.output_path,
            "started_at": self.state.started_at,
            "completed_at": self.state.completed_at,
            "status": self.state.status,
            "current_phase": self.state.current_phase,
            "phases": {
                name: asdict(phase)
                for name, phase in self.state.phases.items()
            },
            "total_files": self.state.total_files,
            "converted_files": self.state.converted_files,
            "failed_files": self.state.failed_files,
            "metadata": self.state.metadata,
        }
        
        self.state_file.write_text(json.dumps(data, indent=2))
    
    def get_phase(self, phase: str) -> Optional[PhaseState]:
        """Get phase state"""
        if not self.state:
            return None
        return self.state.phases.get(phase)
    
    def start_phase(self, phase: str):
        """Mark phase as started"""
        if not self.state:
            return
        
        self.state.current_phase = phase
        
        if phase in self.state.phases:
            phase_state = self.state.phases[phase]
            phase_state.status = PhaseStatus.RUNNING.value
            phase_state.started_at = datetime.now().isoformat()
        
        self.save()
    
    def complete_phase(self, phase: str, files: int = 0, errors: List[str] = None):
        """Mark phase as completed"""
        if not self.state:
            return
        
        if phase in self.state.phases:
            phase_state = self.state.phases[phase]
            phase_state.status = PhaseStatus.COMPLETED.value
            phase_state.completed_at = datetime.now().isoformat()
            phase_state.files_processed = files
            if errors:
                phase_state.errors.extend(errors)
        
        self.save()
    
    def fail_phase(self, phase: str, error: str):
        """Mark phase as failed"""
        if not self.state:
            return
        
        if phase in self.state.phases:
            phase_state = self.state.phases[phase]
            phase_state.status = PhaseStatus.FAILED.value
            phase_state.completed_at = datetime.now().isoformat()
            phase_state.errors.append(error)
        
        self.state.status = "failed"
        
        self.save()
    
    def complete(self, total_files: int, converted: int, failed: int):
        """Mark pipeline as completed"""
        if not self.state:
            return
        
        self.state.status = "completed"
        self.state.completed_at = datetime.now().isoformat()
        self.state.total_files = total_files
        self.state.converted_files = converted
        self.state.failed_files = failed
        
        self.save()
    
    def get_duration(self) -> float:
        """Get pipeline duration in seconds"""
        if not self.state:
            return 0
        
        start = datetime.fromisoformat(self.state.started_at)
        
        if self.state.completed_at:
            end = datetime.fromisoformat(self.state.completed_at)
        else:
            end = datetime.now()
        
        return (end - start).total_seconds()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get state summary"""
        if not self.state:
            return {}
        
        return {
            "status": self.state.status,
            "current_phase": self.state.current_phase,
            "duration_seconds": self.get_duration(),
            "total_files": self.state.total_files,
            "converted_files": self.state.converted_files,
            "failed_files": self.state.failed_files,
            "phases": {
                name: {
                    "status": phase.status,
                    "files": phase.files_processed,
                    "errors": len(phase.errors),
                }
                for name, phase in self.state.phases.items()
            },
        }
    
    def is_resumable(self) -> bool:
        """Check if pipeline can be resumed"""
        if not self.state:
            return False
        
        # Can resume if failed or partially completed
        return self.state.status in ["running", "failed"]
    
    def get_resume_point(self) -> Optional[str]:
        """Get the phase to resume from"""
        if not self.state:
            return None
        
        # Find first incomplete phase
        for phase in PipelinePhase:
            if phase.value in self.state.phases:
                phase_state = self.state.phases[phase.value]
                if phase_state.status != PhaseStatus.COMPLETED.value:
                    return phase.value
        
        return None


# Global state manager
_state_manager: Optional[StateManager] = None


def get_state_manager(state_file: str = None) -> StateManager:
    """Get state manager"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager(state_file)
    return _state_manager
