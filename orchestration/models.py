"""Database models for pipeline data"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("orchestration.models")


class ProjectStatus(Enum):
    """Project status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FileStatus(Enum):
    """File conversion status"""
    PENDING = "pending"
    PROCESSING = "processing"
    CONVERTED = "converted"
    VALIDATED = "validated"
    FAILED = "failed"


@dataclass
class Project:
    """Conversion project"""
    id: int = 0
    name: str = ""
    source_path: str = ""
    output_path: str = ""
    status: str = ProjectStatus.PENDING.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    total_files: int = 0
    converted_files: int = 0
    failed_files: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "source_path": self.source_path,
            "output_path": self.output_path,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "total_files": self.total_files,
            "converted_files": self.converted_files,
            "failed_files": self.failed_files,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Project":
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class ConvertedFile:
    """Converted file record"""
    id: int = 0
    project_id: int = 0
    source_file: str = ""
    output_file: str = ""
    source_format: str = ""
    target_format: str = ""
    status: str = FileStatus.PENDING.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    validated_at: Optional[str] = None
    ai_provider: str = ""
    ai_model: str = ""
    ai_tokens: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "source_file": self.source_file,
            "output_file": self.output_file,
            "source_format": self.source_format,
            "target_format": self.target_format,
            "status": self.status,
            "created_at": self.created_at,
            "validated_at": self.validated_at,
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model,
            "ai_tokens": self.ai_tokens,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class AIUsage:
    """AI API usage record"""
    id: int = 0
    project_id: int = 0
    provider: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at,
        }


@dataclass
class ValidationResult:
    """Validation result"""
    id: int = 0
    file_id: int = 0
    validator: str = ""
    valid: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "file_id": self.file_id,
            "validator": self.validator,
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "created_at": self.created_at,
        }


class InMemoryDB:
    """In-memory database for testing/development"""
    
    def __init__(self):
        self.projects: Dict[int, Project] = {}
        self.files: Dict[int, ConvertedFile] = {}
        self.ai_usage: List[AIUsage] = []
        self.validations: List[ValidationResult] = []
        
        self._project_id = 0
        self._file_id = 0
        self._usage_id = 0
        self._validation_id = 0
    
    # Projects
    def create_project(self, project: Project) -> Project:
        self._project_id += 1
        project.id = self._project_id
        self.projects[project.id] = project
        return project
    
    def get_project(self, project_id: int) -> Optional[Project]:
        return self.projects.get(project_id)
    
    def update_project(self, project: Project) -> bool:
        if project.id in self.projects:
            project.updated_at = datetime.now().isoformat()
            self.projects[project.id] = project
            return True
        return False
    
    def list_projects(self, status: str = None) -> List[Project]:
        projects = list(self.projects.values())
        if status:
            projects = [p for p in projects if p.status == status]
        return projects
    
    # Files
    def create_file(self, file: ConvertedFile) -> ConvertedFile:
        self._file_id += 1
        file.id = self._file_id
        self.files[file.id] = file
        return file
    
    def get_file(self, file_id: int) -> Optional[ConvertedFile]:
        return self.files.get(file_id)
    
    def update_file(self, file: ConvertedFile) -> bool:
        if file.id in self.files:
            self.files[file.id] = file
            return True
        return False
    
    def list_files(self, project_id: int = None, status: str = None) -> List[ConvertedFile]:
        files = list(self.files.values())
        
        if project_id:
            files = [f for f in files if f.project_id == project_id]
        if status:
            files = [f for f in files if f.status == status]
        
        return files
    
    # AI Usage
    def create_usage(self, usage: AIUsage) -> AIUsage:
        self._usage_id += 1
        usage.id = self._usage_id
        self.ai_usage.append(usage)
        return usage
    
    def list_usage(self, project_id: int = None) -> List[AIUsage]:
        if project_id:
            return [u for u in self.ai_usage if u.project_id == project_id]
        return self.ai_usage
    
    def get_usage_stats(self, project_id: int = None) -> Dict:
        usage_list = self.list_usage(project_id)
        
        total_tokens = sum(u.total_tokens for u in usage_list)
        total_cost = sum(u.cost for u in usage_list)
        
        by_provider = {}
        for u in usage_list:
            if u.provider not in by_provider:
                by_provider[u.provider] = {"calls": 0, "tokens": 0, "cost": 0}
            by_provider[u.provider]["calls"] += 1
            by_provider[u.provider]["tokens"] += u.total_tokens
            by_provider[u.provider]["cost"] += u.cost
        
        return {
            "total_calls": len(usage_list),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "by_provider": by_provider,
        }
    
    # Validations
    def create_validation(self, validation: ValidationResult) -> ValidationResult:
        self._validation_id += 1
        validation.id = self._validation_id
        self.validations.append(validation)
        return validation
    
    def list_validations(self, file_id: int = None) -> List[ValidationResult]:
        if file_id:
            return [v for v in self.validations if v.file_id == file_id]
        return self.validations


# Global database
_db: Optional[InMemoryDB] = None


def get_db() -> InMemoryDB:
    """Get database instance"""
    global _db
    if _db is None:
        _db = InMemoryDB()
    return _db
