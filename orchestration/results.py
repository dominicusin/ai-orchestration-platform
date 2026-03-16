"""Pipeline result types and serializers"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger("orchestration.results")


class ResultStatus(str, Enum):
    """Result status"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class FileResult:
    """Single file conversion result"""
    source_file: str
    output_file: str
    status: str
    format: str
    size_bytes: int = 0
    duration_ms: float = 0
    error: Optional[str] = None


@dataclass
class PhaseResult:
    """Phase execution result"""
    phase: str
    status: str
    files_processed: int = 0
    files_failed: int = 0
    duration_ms: float = 0
    file_results: List[FileResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Complete pipeline result"""
    success: bool
    started_at: str
    completed_at: str
    duration_ms: float
    phase_results: List[PhaseResult] = field(default_factory=list)
    total_files: int = 0
    converted_files: int = 0
    failed_files: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PipelineResult":
        return cls(**data)


class ResultSerializer:
    """Serialize/deserialize results"""
    
    @staticmethod
    def to_json(result: PipelineResult) -> str:
        """Serialize to JSON"""
        return result.to_json()
    
    @staticmethod
    def to_dict(result: PipelineResult) -> Dict:
        """Serialize to dict"""
        return result.to_dict()
    
    @staticmethod
    def from_json(json_str: str) -> PipelineResult:
        """Deserialize from JSON"""
        data = json.loads(json_str)
        return PipelineResult.from_dict(data)
    
    @staticmethod
    def save(result: PipelineResult, path: str):
        """Save to file"""
        with open(path, "w") as f:
            f.write(result.to_json())
    
    @staticmethod
    def load(path: str) -> PipelineResult:
        """Load from file"""
        with open(path, "r") as f:
            return ResultSerializer.from_json(f.read())
